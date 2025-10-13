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
from psycopg2.extras import RealDictCursor
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
            self.init_database()
            logger.info("✅ PostgreSQL دیتابیس با موفقیت مقداردهی شد")
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
                    message_count INTEGER DEFAULT 0
                )
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
            
            conn.commit()
            logger.info("✅ جداول دیتابیس ایجاد شدند")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ایجاد جداول: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """افزودن کاربر جدید"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_activity = CURRENT_TIMESTAMP
            ''', (user_id, username, first_name, last_name))
            
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
            
            return dict(result) if result else None
            
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
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران: {e}")
            return []
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
    
    def log_system_event(self, event: str, details: str = None):
        """ثبت رویداد سیستم"""
        try:
            self.db.log_event(0, event, details)  # user_id=0 برای رویدادهای سیستم
            self.logger.info(f"Event: {event} | Details: {details}")
        except Exception as e:
            self.logger.error(f"❌ خطا در ثبت رویداد: {e}")
