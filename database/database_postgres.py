#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
مدیریت دیتابیس PostgreSQL برای ربات تلگرام
این ماژول شامل تمام عملیات مربوط به دیتابیس PostgreSQL است
"""

import os
import logging
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2 import pool
import datetime
from typing import Optional, List, Tuple, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    def __init__(self, database_url: str = None):
        """مقداردهی مدیر دیتابیس PostgreSQL"""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Parse database URL
        parsed = urlparse(self.database_url)
        self.connection_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'  # Required for Supabase
        }
        
        # Create connection pool
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,  # min and max connections
                **self.connection_params
            )
            # بررسی اینکه آیا دیتابیس قبلاً مقداردهی شده یا نه
            is_first_run = self.is_first_database_run()
            self.init_database()
            if is_first_run:
                logger.info("✅ PostgreSQL دیتابیس با موفقیت مقداردهی شد")
            else:
                logger.debug("✅ PostgreSQL دیتابیس متصل شد")
        except Exception as e:
            logger.error(f"❌ خطا در اتصال به PostgreSQL: {e}")
            raise

    def get_connection(self):
        """دریافت اتصال از pool"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """بازگردانی اتصال به pool"""
        self.connection_pool.putconn(conn)

    def init_database(self):
        """ایجاد جداول اولیه دیتابیس"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # جدول کاربران
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    spam_warnings INTEGER DEFAULT 0,
                    block_until TIMESTAMP NULL,
                    block_reason TEXT NULL
                )
            ''')
            
            # جدول tracking پیام‌ها برای anti-spam
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_message_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_type TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # ایجاد index برای بهبود performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_tracking_user_time 
                ON user_message_tracking(user_id, message_time DESC)
            ''')
            
            # جدول لاگ‌ها  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id BIGINT,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            # جدول تنظیمات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول آمار
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_statistics (
                    id SERIAL PRIMARY KEY,
                    date DATE DEFAULT CURRENT_DATE,
                    total_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    messages_sent INTEGER DEFAULT 0,
                    commands_used INTEGER DEFAULT 0
                )
            ''')
            
            # جدول تاریخچه چت با AI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    role TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # Index برای بهبود performance تاریخچه
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_history_user_time
                ON ai_chat_history(user_id, timestamp DESC)
            ''')

            # جدول کش برنامه هفتگی بازی‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sports_weekly_fixtures_cache (
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    payload JSONB NOT NULL,
                    fetched_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (week_start, week_end)
                )
            ''')
            
            # تنظیمات پیش‌فرض
            cursor.execute('''
                INSERT INTO bot_settings (key, value, description)
                VALUES 
                    ('bot_enabled', '1', 'Bot enabled/disabled status'),
                    ('maintenance_mode', '0', 'Maintenance mode status'),
                    ('welcome_message', 'سلام! به ربات خوش آمدید', 'Welcome message'),
                    ('total_messages', '0', 'Total messages count')
                ON CONFLICT (key) DO NOTHING
            ''')
            
            # 🔄 Migration: اضافه کردن ستون‌های Anti-Spam به جداول موجود
            try:
                # بررسی وجود ستون spam_warnings
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='spam_warnings'
                """)
                if not cursor.fetchone():
                    cursor.execute('ALTER TABLE users ADD COLUMN spam_warnings INTEGER DEFAULT 0')
                    logger.info("✅ ستون spam_warnings اضافه شد")
                
                # بررسی وجود ستون block_until
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='block_until'
                """)
                if not cursor.fetchone():
                    cursor.execute('ALTER TABLE users ADD COLUMN block_until TIMESTAMP NULL')
                    logger.info("✅ ستون block_until اضافه شد")
                
                # بررسی وجود ستون block_reason
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='block_reason'
                """)
                if not cursor.fetchone():
                    cursor.execute('ALTER TABLE users ADD COLUMN block_reason TEXT NULL')
                    logger.info("✅ ستون block_reason اضافه شد")
                    
            except Exception as migration_error:
                logger.warning(f"⚠️ Migration warning: {migration_error}")
            
            conn.commit()
            
            # فقط در صورتی که اولین بار باشد این پیام نمایش داده شود
            if self.is_first_database_run():
                logger.info("✅ جداول دیتابیس ایجاد شدند")
                # علامت‌گذاری دیتابیس به عنوان مقداردهی شده
                self.mark_database_initialized()
            else:
                logger.debug("🔄 جداول دیتابیس بررسی شدند")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ایجاد جداول: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def remove_sports_favorite_team_by_id(self, user_id: int, team_id: int) -> Tuple[bool, str]:
        """حذف تیم مورد علاقه کاربر بر اساس شناسه تیم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                DELETE FROM sports_favorite_teams
                WHERE user_id = %s AND team_id = %s
                ''',
                (user_id, team_id)
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "این تیم در لیست شما پیدا نشد"

            conn.commit()
            return True, "تیم از لیست شما حذف شد"

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در حذف تیم کاربر {user_id} با شناسه {team_id}: {e}")
            return False, "خطا در حذف تیم"
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def delete_match_reminders_for_team(self, user_id: int, team_id: int) -> bool:
        """حذف یادآوری‌های مرتبط با یک تیم برای کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM sports_match_reminders WHERE user_id = %s AND team_id = %s',
                (user_id, team_id)
            )

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در حذف یادآوری‌های تیم {team_id} برای کاربر {user_id}: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def delete_user_match_reminders(self, user_id: int) -> bool:
        """حذف تمام یادآوری‌های یک کاربر (مثلاً هنگام پاک کردن همه تیم‌ها)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM sports_match_reminders WHERE user_id = %s',
                (user_id,)
            )

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در حذف یادآوری‌های کاربر {user_id}: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_user_match_reminders(self, user_id: int, include_sent: bool = False) -> List[Dict[str, Any]]:
        """دریافت یادآوری‌های کاربر (تنها pending یا همراه با ارسال شده‌ها)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if include_sent:
                cursor.execute(
                    '''
                    SELECT * FROM sports_match_reminders
                    WHERE user_id = %s
                    ORDER BY reminder_datetime ASC
                    ''',
                    (user_id,)
                )
            else:
                cursor.execute(
                    '''
                    SELECT * FROM sports_match_reminders
                    WHERE user_id = %s AND status = 'pending'
                    ORDER BY reminder_datetime ASC
                    ''',
                    (user_id,)
                )

            reminders = cursor.fetchall()
            return [dict(row) for row in reminders]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت یادآوری‌های کاربر {user_id}: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def upsert_weekly_fixtures_cache(self, week_start: datetime.date, week_end: datetime.date,
                                     payload: Dict[str, Any]) -> bool:
        """ذخیره یا به‌روزرسانی کش فیکسچر هفتگی"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO sports_weekly_fixtures_cache (week_start, week_end, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (week_start, week_end)
                DO UPDATE SET payload = EXCLUDED.payload,
                              fetched_at = NOW()
                ''',
                (week_start, week_end, Json(payload))
            )

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ذخیره کش فیکسچر هفتگی: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_weekly_fixtures_cache(self, week_start: datetime.date,
                                  week_end: datetime.date) -> Optional[Dict[str, Any]]:
        """دریافت کش فیکسچر هفتگی"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                '''
                SELECT payload, fetched_at
                FROM sports_weekly_fixtures_cache
                WHERE week_start = %s AND week_end = %s
                ''',
                (week_start, week_end)
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'payload': row['payload'],
                'fetched_at': row['fetched_at']
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت کش فیکسچر هفتگی: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    def is_first_database_run(self) -> bool:
        """بررسی اینکه آیا این اولین بار اجرای دیتابیس است یا نه"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # بررسی وجود جدول system_info
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'system_info'
                )
            """)
            
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                cursor.close()
                self.return_connection(conn)
                return True  # اولین بار است
                
            # بررسی علامت‌گذاری اولیه
            cursor.execute("""
                SELECT value FROM system_info WHERE key = 'database_initialized'
            """)
            
            result = cursor.fetchone()
            cursor.close()
            self.return_connection(conn)
            
            # اگر علامت‌گذاری وجود نداشته باشد، اولین بار است
            return result is None
            
        except Exception as e:
            logger.warning(f"⚠️ خطا در بررسی وضعیت اولیه دیتابیس: {e}")
            return True  # در صورت خطا، فرض می‌کنیم اولین بار است

    def mark_database_initialized(self):
        """علامت‌گذاری دیتابیس به عنوان مقداردهی شده"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # ایجاد جدول system_info اگر وجود نداشته باشد
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_info (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ثبت علامت‌گذاری
            cursor.execute('''
                INSERT INTO system_info (key, value)
                VALUES ('database_initialized', 'true')
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    created_at = CURRENT_TIMESTAMP
            ''')
            
            conn.commit()
            cursor.close()
            self.return_connection(conn)
            
        except Exception as e:
            logger.warning(f"⚠️ خطا در علامت‌گذاری دیتابیس: {e}")

    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, is_admin: bool = False) -> bool:
        """افزودن کاربر جدید"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, is_admin)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    is_admin = EXCLUDED.is_admin,
                    last_activity = CURRENT_TIMESTAMP
            ''', (user_id, username, first_name, last_name, is_admin))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در افزودن کاربر: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_user(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone()
            
            if result:
                user_dict = dict(result)
                # تبدیل datetime objects به string
                if user_dict.get('join_date'):
                    user_dict['join_date'] = user_dict['join_date'].strftime('%Y-%m-%d %H:%M:%S')
                if user_dict.get('last_activity'):
                    user_dict['last_activity'] = user_dict['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
                return user_dict
            return None
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربر: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def update_user_activity(self, user_id: int) -> bool:
        """به‌روزرسانی فعالیت کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_activity = CURRENT_TIMESTAMP, 
                    message_count = message_count + 1
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در به‌روزرسانی فعالیت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_all_users(self) -> List[Dict]:
        """دریافت تمام کاربران"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
            results = cursor.fetchall()
            
            # تبدیل datetime objects به string برای سازگاری
            users = []
            for row in results:
                user_dict = dict(row)
                # تبدیل join_date به string
                if user_dict.get('join_date'):
                    user_dict['join_date'] = user_dict['join_date'].strftime('%Y-%m-%d %H:%M:%S')
                # تبدیل last_activity به string
                if user_dict.get('last_activity'):
                    user_dict['last_activity'] = user_dict['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
                users.append(user_dict)
            
            return users
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    # -----------------------------
    # 📌 مدیریت تیم‌های مورد علاقه ورزشی
    # -----------------------------

    def get_sports_favorite_teams(self, user_id: int) -> List[Dict[str, Any]]:
        """دریافت تیم‌های مورد علاقه یک کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                '''
                SELECT id, league_id, league_name, team_id, team_name, created_at
                FROM sports_favorite_teams
                WHERE user_id = %s
                ORDER BY created_at DESC
                ''',
                (user_id,)
            )

            teams = cursor.fetchall()
            return [dict(row) for row in teams]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت تیم‌های مورد علاقه کاربر {user_id}: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def add_sports_favorite_team(self, user_id: int, league_id: int, league_name: str,
                                 team_id: int, team_name: str, max_teams: int = 10,
                                 bypass_limit: bool = False) -> Tuple[bool, str]:
        """افزودن تیم مورد علاقه برای کاربر (با محدودیت ۱۰ تیم)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if not bypass_limit:
                cursor.execute(
                    'SELECT COUNT(*) FROM sports_favorite_teams WHERE user_id = %s',
                    (user_id,)
                )
                count = cursor.fetchone()[0]
                if count >= max_teams:
                    return False, "شما حداکثر تعداد تیم مجاز را ثبت کرده‌اید"

            try:
                cursor.execute(
                    '''
                    INSERT INTO sports_favorite_teams
                        (user_id, league_id, league_name, team_id, team_name)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, team_id) DO NOTHING
                    ''',
                    (user_id, league_id, league_name, team_id, team_name)
                )
                if cursor.rowcount == 0:
                    return False, "این تیم قبلاً در لیست شما وجود دارد"

                conn.commit()
                return True, "تیم با موفقیت به لیست اضافه شد"

            except Exception as e:
                conn.rollback()
                logger.error(f"❌ خطا در افزودن تیم مورد علاقه برای کاربر {user_id}: {e}")
                return False, "خطا در ذخیره تیم"

        except Exception as e:
            logger.error(f"❌ خطای اتصال در افزودن تیم مورد علاقه: {e}")
            return False, "مشکل در ارتباط با دیتابیس"
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def remove_sports_favorite_team(self, user_id: int, team_name: str) -> Tuple[bool, str]:
        """حذف تیم مورد علاقه کاربر بر اساس نام"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                DELETE FROM sports_favorite_teams
                WHERE user_id = %s AND team_name = %s
                ''',
                (user_id, team_name)
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "این تیم در لیست شما پیدا نشد"

            conn.commit()
            return True, "تیم از لیست شما حذف شد"

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در حذف تیم کاربر {user_id}: {e}")
            return False, "خطا در حذف تیم"
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def clear_sports_favorites(self, user_id: int) -> bool:
        """حذف تمام تیم‌های مورد علاقه کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM sports_favorite_teams WHERE user_id = %s',
                (user_id,)
            )

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در پاک کردن تیم‌های کاربر {user_id}: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_users_with_sports_favorites(self) -> List[int]:
        """کاربرانی که حداقل یک تیم مورد علاقه دارند"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                'SELECT DISTINCT user_id FROM sports_favorite_teams'
            )

            rows = cursor.fetchall()
            return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران دارای تیم مورد علاقه: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    # -----------------------------
    # 🕒 مدیریت یادآوری بازی‌ها
    # -----------------------------

    def create_match_reminder(self, user_id: int, fixture_id: int, team_id: int,
                              team_name: str, opponent_team_id: int,
                              opponent_team_name: str, league_id: int,
                              league_name: str, match_datetime: datetime.datetime,
                              reminder_datetime: datetime.datetime,
                              extra_info: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """ایجاد یادآور بازی برای یک کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                INSERT INTO sports_match_reminders
                    (user_id, fixture_id, team_id, team_name, opponent_team_id,
                     opponent_team_name, league_id, league_name, match_datetime,
                     reminder_datetime, extra_info)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, fixture_id) DO NOTHING
                ''',
                (
                    user_id, fixture_id, team_id, team_name,
                    opponent_team_id, opponent_team_name,
                    league_id, league_name,
                    match_datetime, reminder_datetime,
                    extra_info or {}
                )
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return False, "این بازی قبلاً در لیست یادآور شما ثبت شده است"

            conn.commit()
            return True, "یادآوری بازی ثبت شد"

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ایجاد یادآوری بازی برای کاربر {user_id}: {e}")
            return False, "خطا در ثبت یادآوری"
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_pending_match_reminders(self, before_datetime: datetime.datetime) -> List[Dict[str, Any]]:
        """دریافت یادآوری‌های در انتظار تا زمان مشخص"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                '''
                SELECT * FROM sports_match_reminders
                WHERE status = 'pending' AND reminder_datetime <= %s
                ORDER BY reminder_datetime ASC
                ''',
                (before_datetime,)
            )

            reminders = cursor.fetchall()
            return [dict(row) for row in reminders]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت یادآوری‌های در انتظار: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def mark_match_reminder_sent(self, reminder_id: int) -> bool:
        """علامت‌گذاری یادآوری به عنوان ارسال‌شده"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                UPDATE sports_match_reminders
                SET status = 'sent', sent_at = NOW()
                WHERE id = %s
                ''',
                (reminder_id,)
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return False

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت یادآوری {reminder_id}: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def cancel_match_reminder(self, reminder_id: int) -> bool:
        """لغو یادآوری"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                UPDATE sports_match_reminders
                SET status = 'cancelled'
                WHERE id = %s
                ''',
                (reminder_id,)  # Fixed the parameter tuple here
            )

            if cursor.rowcount == 0:
                conn.rollback()
                return False

            conn.commit()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در لغو یادآوری {reminder_id}: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_user_count(self) -> int:
        """دریافت تعداد کاربران"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            
            return count
            
        except Exception as e:
            logger.error(f"❌ خطا در شمارش کاربران: {e}")
            return 0
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_user_stats(self) -> Dict[str, int]:
        """دریافت آمار کاربران"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # تعداد کل کاربران
            cursor.execute('SELECT COUNT(*) FROM users')
            total = cursor.fetchone()[0]
            
            # کاربران فعال (غیربلاک + فعالیت در 24 ساعت گذشته)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE is_blocked = FALSE 
                AND last_activity >= NOW() - INTERVAL '24 hours'
            ''')
            active = cursor.fetchone()[0]
            
            # کاربران بلاک شده
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = TRUE')
            blocked = cursor.fetchone()[0]
            
            # کاربران امروز
            cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(join_date) = CURRENT_DATE')
            today_users = cursor.fetchone()[0]
            
            # کل پیام‌ها
            cursor.execute('SELECT COALESCE(SUM(message_count), 0) FROM users')
            total_messages = cursor.fetchone()[0]
            
            return {
                'total': total,
                'active': active,
                'blocked': blocked,
                'today': today_users,
                'total_messages': total_messages
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار کاربران: {e}")
            return {'total': 0, 'active': 0, 'blocked': 0, 'today': 0, 'total_messages': 0}
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def block_user(self, user_id: int) -> bool:
        """مسدود کردن کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET is_blocked = TRUE WHERE user_id = %s', (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در مسدود کردن کاربر: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def unblock_user(self, user_id: int) -> bool:
        """رفع مسدودیت کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET is_blocked = FALSE WHERE user_id = %s', (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در رفع مسدودیت کاربر: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def is_user_blocked(self, user_id: int) -> bool:
        """بررسی بلاک بودن کاربر (همراه با چک کردن زمان)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                'SELECT is_blocked, block_until FROM users WHERE user_id = %s', 
                (user_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            
            # اگر بلاک نیست، False برگردون
            if not result['is_blocked']:
                return False
            
            # اگر block_until تنظیم نشده (بلاک دائمی)، True برگردون
            if not result['block_until']:
                return True
            
            # چک کردن آیا زمان بلاک تموم شده یا نه
            import datetime
            if result['block_until'] <= datetime.datetime.now():
                # زمان بلاک تموم شده، خودکار آنبلاک کن
                cursor.execute(
                    'UPDATE users SET is_blocked = FALSE, block_until = NULL WHERE user_id = %s',
                    (user_id,)
                )
                conn.commit()
                logger.info(f"✅ کاربر {user_id} به صورت خودکار آنبلاک شد")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در بررسی وضعیت بلاک کاربر: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_active_users_ids(self) -> List[int]:
        """دریافت ID های کاربران فعال (غیربلاک و در 24 ساعت گذشته فعالیت داشته باشند)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # کاربران فعال = غیربلاک + فعالیت در 24 ساعت گذشته
            cursor.execute('''
                SELECT user_id FROM users 
                WHERE is_blocked = FALSE 
                AND last_activity >= NOW() - INTERVAL '24 hours'
            ''')
            results = cursor.fetchall()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران فعال: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_all_unblocked_users_ids(self) -> List[int]:
        """دریافت ID های همه کاربران غیربلاک (برای broadcast)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT user_id FROM users WHERE is_blocked = FALSE')
            results = cursor.fetchall()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران غیربلاک: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def log_event(self, user_id: int, event_type: str, details: str = None) -> bool:
        """ثبت رویداد در لاگ"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_logs (user_id, event_type, details)
                VALUES (%s, %s, %s)
            ''', (user_id, event_type, details))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ثبت لاگ: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """دریافت لاگ‌های اخیر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT * FROM bot_logs 
                ORDER BY timestamp DESC 
                LIMIT %s
            ''', (limit,))
            results = cursor.fetchall()
            
            # تبدیل timestamp به string
            logs = []
            for row in results:
                log_dict = dict(row)
                if log_dict.get('timestamp'):
                    log_dict['timestamp'] = log_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                logs.append(log_dict)
            
            return logs
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لاگ‌ها: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_setting(self, key: str) -> Optional[str]:
        """دریافت تنظیم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('SELECT value FROM bot_settings WHERE key = %s', (key,))
            result = cursor.fetchone()
            
            return result['value'] if result else None
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تنظیم: {e}")
            return None
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def set_setting(self, key: str, value: str) -> bool:
        """تنظیم یک تنظیم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_settings (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, value))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در تنظیم: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def is_bot_enabled(self) -> bool:
        """بررسی فعال بودن ربات"""
        return self.get_setting('bot_enabled') == '1'

    def set_bot_enabled(self, enabled: bool) -> bool:
        """تنظیم وضعیت ربات"""
        return self.set_setting('bot_enabled', '1' if enabled else '0')

    def track_user_message(self, user_id: int, message_type: str = 'text') -> bool:
        """ثبت پیام کاربر برای tracking اسپم"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO user_message_tracking (user_id, message_type) VALUES (%s, %s)',
                (user_id, message_type)
            )
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ثبت tracking پیام: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_recent_message_count(self, user_id: int, seconds: int = 15) -> int:
        """دریافت تعداد پیام‌های اخیر کاربر در N ثانیه گذشته"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM user_message_tracking 
                WHERE user_id = %s 
                AND message_time >= NOW() - INTERVAL '%s seconds'
            ''', (user_id, seconds))
            
            count = cursor.fetchone()[0]
            return count
            
        except Exception as e:
            logger.error(f"❌ خطا در شمارش پیام‌های اخیر: {e}")
            return 0
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def cleanup_old_message_tracking(self, hours: int = 24) -> bool:
        """پاک کردن رکوردهای قدیمی tracking (بیش از N ساعت)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM user_message_tracking WHERE message_time < NOW() - INTERVAL '%s hours'",
                (hours,)
            )
            conn.commit()
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(f"🗑️ {deleted_count} رکورد قدیمی tracking پاک شد")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در پاک کردن tracking قدیمی: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def block_user_for_spam(self, user_id: int) -> Dict[str, any]:
        """بلاک کردن کاربر به دلیل اسپم (با سطح‌بندی زمانی)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # دریافت تعداد warnings قبلی
            cursor.execute(
                'SELECT spam_warnings FROM users WHERE user_id = %s',
                (user_id,)
            )
            result = cursor.fetchone()
            
            current_warnings = result['spam_warnings'] if result else 0
            new_warnings = current_warnings + 1
            
            # تعیین مدت زمان بلاک
            import datetime
            if new_warnings == 1:
                # اولین بار: 1 روز
                block_duration = datetime.timedelta(days=1)
                block_level = "1 روز"
            elif new_warnings == 2:
                # دومین بار: 1 هفته
                block_duration = datetime.timedelta(days=7)
                block_level = "1 هفته"
            else:
                # سومین بار و بعد: دائمی
                block_duration = None
                block_level = "دائمی"
            
            # محاسبه زمان پایان بلاک
            if block_duration:
                block_until = datetime.datetime.now() + block_duration
            else:
                block_until = None
            
            # بلاک کردن کاربر
            cursor.execute('''
                UPDATE users 
                SET is_blocked = TRUE, 
                    spam_warnings = %s, 
                    block_until = %s,
                    block_reason = 'spam'
                WHERE user_id = %s
            ''', (new_warnings, block_until, user_id))
            
            conn.commit()
            
            logger.warning(f"🚫 کاربر {user_id} به دلیل اسپم بلاک شد (سطح {new_warnings}: {block_level})")
            
            return {
                'success': True,
                'warning_level': new_warnings,
                'block_duration': block_level,
                'block_until': block_until,
                'is_permanent': block_duration is None
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در بلاک کردن کاربر: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_blocked_users_with_time(self) -> List[Dict]:
        """دریافت لیست کاربران بلاک شده همراه با زمان"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT user_id, username, first_name, 
                       spam_warnings, block_until, block_reason
                FROM users 
                WHERE is_blocked = TRUE
                ORDER BY block_until ASC NULLS LAST
            ''')
            
            results = cursor.fetchall()
            
            blocked_users = []
            for row in results:
                user_dict = dict(row)
                if user_dict.get('block_until'):
                    user_dict['block_until'] = user_dict['block_until'].strftime('%Y-%m-%d %H:%M:%S')
                blocked_users.append(user_dict)
            
            return blocked_users
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران بلاک شده: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def manual_unblock_user(self, user_id: int) -> bool:
        """آنبلاک دستی کاربر (بدون تغییر spam_warnings)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_blocked = FALSE, 
                    block_until = NULL
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            logger.info(f"✅ کاربر {user_id} به صورت دستی آنبلاک شد")
            return cursor.rowcount > 0
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در آنبلاک دستی کاربر: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def auto_unblock_expired_users(self) -> int:
        """آنبلاک خودکار کاربرهایی که زمان بلاکشان تمام شده"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            import datetime
            cursor.execute('''
                UPDATE users 
                SET is_blocked = FALSE, 
                    block_until = NULL
                WHERE is_blocked = TRUE 
                AND block_until IS NOT NULL 
                AND block_until <= %s
            ''', (datetime.datetime.now(),))
            
            conn.commit()
            
            unblocked_count = cursor.rowcount
            if unblocked_count > 0:
                logger.info(f"✅ {unblocked_count} کاربر به صورت خودکار آنبلاک شدند")
            
            return unblocked_count
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در آنبلاک خودکار: {e}")
            return 0
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def add_chat_message(self, user_id: int, role: str, message_text: str) -> bool:
        """اضافه کردن پیام به تاریخچه چت"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ai_chat_history (user_id, role, message_text)
                VALUES (%s, %s, %s)
            ''', (user_id, role, message_text))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ذخیره پیام چت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict[str, str]]:
        """دریافت تاریخچه چت کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT role, message_text, timestamp
                FROM ai_chat_history
                WHERE user_id = %s
                ORDER BY timestamp ASC
                LIMIT %s
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            
            # تبدیل به لیست dictionary
            history = []
            for row in results:
                history.append({
                    'role': row['role'],
                    'message_text': row['message_text']
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاریخچه چت: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def clear_chat_history(self, user_id: int) -> bool:
        """پاک کردن تاریخچه چت کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'DELETE FROM ai_chat_history WHERE user_id = %s',
                (user_id,)
            )
            
            conn.commit()
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.info(f"🗑️ {deleted_count} پیام از تاریخچه کاربر {user_id} پاک شد")
            
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در پاک کردن تاریخچه چت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_chat_history_count(self, user_id: int) -> int:
        """دریافت تعداد پیام‌های تاریخچه چت"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT COUNT(*) FROM ai_chat_history WHERE user_id = %s',
                (user_id,)
            )
            
            count = cursor.fetchone()[0]
            return count
            
        except Exception as e:
            logger.error(f"❌ خطا در شمارش تاریخچه چت: {e}")
            return 0
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def enable_news_subscription(self, user_id: int) -> bool:
        """فعال کردن اشتراک اخبار برای کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE users SET news_subscription_enabled = TRUE WHERE user_id = %s',
                (user_id,)
            )
            
            conn.commit()
            logger.info(f"✅ اشتراک اخبار برای کاربر {user_id} فعال شد")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در فعال‌سازی اشتراک اخبار: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def disable_news_subscription(self, user_id: int) -> bool:
        """غیرفعال کردن اشتراک اخبار برای کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE users SET news_subscription_enabled = FALSE WHERE user_id = %s',
                (user_id,)
            )
            
            conn.commit()
            logger.info(f"✅ اشتراک اخبار برای کاربر {user_id} غیرفعال شد")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در غیرفعال‌سازی اشتراک اخبار: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def is_news_subscribed(self, user_id: int) -> bool:
        """بررسی وضعیت اشتراک اخبار کاربر"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT news_subscription_enabled FROM users WHERE user_id = %s',
                (user_id,)
            )
            
            result = cursor.fetchone()
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"❌ خطا در بررسی وضعیت اشتراک: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def get_news_subscribers(self) -> list:
        """دریافت لیست کاربران مشترک اخبار (فعال و غیربلاک شده)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT user_id FROM users WHERE news_subscription_enabled = TRUE AND is_blocked = FALSE'
            )
            
            subscribers = [row[0] for row in cursor.fetchall()]
            logger.info(f"👥 تعداد مشترکان اخبار: {len(subscribers)}")
            return subscribers
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست مشترکان: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def close(self):
        """بستن pool اتصالات"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            logger.info("🔒 اتصالات دیتابیس بسته شدند")


class DatabaseLogger:
    """کلاس برای لاگ کردن فعالیت‌های ربات"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
        self.logger = logging.getLogger('bot_system')
    
    def log_user_activity(self, user_id: int, activity: str, details: str = None):
        """ثبت فعالیت کاربر"""
        try:
            self.db.log_event(user_id, activity, details)
            self.logger.info(f"User: {user_id} | Activity: {activity} | Details: {details}")
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت فعالیت: {e}")
    
    def log_user_action(self, user_id: int, action: str, message: str = ""):
        """لاگ عملیات کاربر (سازگار با SQLite)"""
        try:
            details = f"{message} - Action: {action}" if message else action
            self.db.log_event(user_id, 'USER_ACTION', details)
            self.logger.info(f"User: {user_id} | Action: {action} | Message: {message}")
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت عملیات کاربر: {e}")
    
    def log_admin_action(self, admin_id: int, action: str, target_user: int = None, target: str = None, details: str = None):
        """لاگ عملیات ادمین (سازگار با SQLite)"""
        try:
            msg = f"Admin {admin_id} performed: {action}"
            if target_user:
                msg += f" on user {target_user}"
            elif target:
                msg += f" | Target: {target}"
            if details:
                msg += f" | Details: {details}"
            
            self.db.log_event(admin_id, 'ADMIN_ACTION', msg)
            self.logger.info(msg)
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت عملیات ادمین: {e}")
    
    def log_system_event(self, event: str, details: str = None):
        """ثبت رویداد سیستم"""
        try:
            self.db.log_event(0, event, details)  # user_id=0 برای رویدادهای سیستم
            self.logger.info(f"Event: {event} | Details: {details}")
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت رویداد: {e}")
    
    def log_error(self, error_msg: str, error: Exception = None):
        """ثبت خطا"""
        try:
            details = f"{error_msg} | Exception: {str(error)}" if error else error_msg
            self.db.log_event(0, 'ERROR', details)
            self.logger.error(details)
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت خطا: {e}")
