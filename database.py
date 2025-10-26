#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
مدیریت دیتابیس برای ربات تلگرام
این ماژول شامل تمام عملیات مربوط به دیتابیس و مدیریت کاربران است
"""

import sqlite3
import datetime
import logging
import os
import tempfile
from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Singleton pattern برای جلوگیری از ایجاد چندین instance
_db_manager_instance = None

def get_database_manager():
    """دریافت singleton instance از DatabaseManager"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance

class DatabaseManager:
    def __init__(self, db_path: str = "bot_database.db"):
        """مقداردهی مدیر دیتابیس"""
        # در محیط production، اگر نتوان فایل ایجاد کرد، از حافظه استفاده کن
        try:
            # تست کن که آیا می‌توان فایل ایجاد کرد
            test_path = f"{db_path}.test"
            with open(test_path, 'w') as f:
                f.write('test')
            os.remove(test_path)
            self.db_path = db_path
        except (PermissionError, OSError):
            # اگر نتوان فایل ایجاد کرد، از دیتابیس حافظه‌ای استفاده کن
            logger.warning("Cannot create database file, using in-memory database")
            self.db_path = ":memory:"
            
        self.init_database()
    
    def get_connection(self):
        """ایجاد اتصال به دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # برای دسترسی به نتایج به صورت dictionary
        return conn
    
    def init_database(self):
        """ایجاد جداول اولیه دیتابیس"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # جدول کاربران
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        is_blocked INTEGER DEFAULT 0,
                        block_until TIMESTAMP NULL,
                        is_admin INTEGER DEFAULT 0,
                        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        news_subscription_enabled INTEGER DEFAULT 0
                    )
                ''')
                
                # اضافه کردن ستون block_until اگر وجود نداشته باشد
                try:
                    cursor.execute('SELECT block_until FROM users LIMIT 1')
                except:
                    cursor.execute('ALTER TABLE users ADD COLUMN block_until TIMESTAMP NULL')
                    logger.info("✅ ستون block_until به جدول users اضافه شد")
                
                # جدول لاگ‌ها
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        user_id INTEGER,
                        action TEXT
                    )
                ''')
                
                # جدول تنظیمات ربات
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # تنظیمات پیش‌فرض
                cursor.execute('''
                    INSERT OR IGNORE INTO bot_settings (key, value) VALUES 
                    ('bot_enabled', '1'),
                    ('maintenance_mode', '0'),
                    ('welcome_message', 'سلام! به ربات خوش آمدید'),
                    ('total_messages', '0')
                ''')
                
                conn.commit()
                logger.info("دیتابیس با موفقیت مقداردهی شد")
                
                # تست کن که جدول users واقعاً وجود داشته باشد
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    logger.info("✅ جدول users تأیید شد")
                else:
                    logger.error("❌ جدول users یافت نشد!")
                    
        except Exception as e:
            logger.error(f"خطا در مقداردهی دیتابیس: {e}")
            raise e  # Re-raise to make the error visible
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, 
                 last_name: str = None, is_admin: bool = False) -> bool:
        """اضافه کردن کاربر جدید"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, is_admin, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, last_name, 1 if is_admin else 0, 
                      datetime.datetime.now()))
                conn.commit()
                logger.info(f"کاربر {user_id} به دیتابیس اضافه شد")
                return True
        except Exception as e:
            logger.error(f"خطا در اضافه کردن کاربر: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"خطا در دریافت کاربر: {e}")
            return None
    
    def update_user_activity(self, user_id: int):
        """به‌روزرسانی آخرین فعالیت کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET last_activity = ?, message_count = message_count + 1
                    WHERE user_id = ?
                ''', (datetime.datetime.now(), user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی فعالیت کاربر: {e}")
    
    def block_user(self, user_id: int) -> bool:
        """بلاک کردن کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
                logger.info(f"کاربر {user_id} بلاک شد")
                return True
        except Exception as e:
            logger.error(f"خطا در بلاک کردن کاربر: {e}")
            return False
    
    def unblock_user(self, user_id: int) -> bool:
        """انبلاک کردن کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
                conn.commit()
                logger.info(f"کاربر {user_id} انبلاک شد")
                return True
        except Exception as e:
            logger.error(f"خطا در انبلاک کردن کاربر: {e}")
            return False
    
    def is_user_blocked(self, user_id: int) -> bool:
        """بررسی بلاک بودن کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return bool(result['is_blocked']) if result else False
        except Exception as e:
            logger.error(f"خطا در بررسی وضعیت بلاک کاربر: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """دریافت تمام کاربران"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطا در دریافت تمام کاربران: {e}")
            return []
    
    def get_active_users_ids(self) -> List[int]:
        """دریافت ID های کاربران فعال (غیر بلاک شده)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0')
                return [row['user_id'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطا در دریافت کاربران فعال: {e}")
            return []
    
    def get_user_stats(self) -> Dict[str, int]:
        """دریافت آمار کاربران"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # تعداد کل کاربران
                cursor.execute('SELECT COUNT(*) as total FROM users')
                total = cursor.fetchone()['total']
                
                # کاربران فعال
                cursor.execute('SELECT COUNT(*) as active FROM users WHERE is_blocked = 0')
                active = cursor.fetchone()['active']
                
                # کاربران بلاک شده
                cursor.execute('SELECT COUNT(*) as blocked FROM users WHERE is_blocked = 1')
                blocked = cursor.fetchone()['blocked']
                
                # کاربران امروز
                today = datetime.date.today()
                cursor.execute('SELECT COUNT(*) as today FROM users WHERE DATE(join_date) = ?', (today,))
                today_users = cursor.fetchone()['today']
                
                # کل پیام‌ها
                cursor.execute('SELECT SUM(message_count) as total_messages FROM users')
                total_messages = cursor.fetchone()['total_messages'] or 0
                
                return {
                    'total': total,
                    'active': active,
                    'blocked': blocked,
                    'today': today_users,
                    'total_messages': total_messages
                }
        except Exception as e:
            logger.error(f"خطا در دریافت آمار کاربران: {e}")
            return {'total': 0, 'active': 0, 'blocked': 0, 'today': 0, 'total_messages': 0}
    
    def add_log(self, level: str, message: str, user_id: int = None, action: str = None):
        """اضافه کردن لاگ"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO logs (level, message, user_id, action)
                    VALUES (?, ?, ?, ?)
                ''', (level, message, user_id, action))
                conn.commit()
        except Exception as e:
            logger.error(f"خطا در اضافه کردن لاگ: {e}")
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """دریافت لاگ‌های اخیر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطا در دریافت لاگ‌ها: {e}")
            return []
    
    def get_setting(self, key: str) -> Optional[str]:
        """دریافت تنظیم"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
                result = cursor.fetchone()
                return result['value'] if result else None
        except Exception as e:
            logger.error(f"خطا در دریافت تنظیم: {e}")
            return None
    
    def set_setting(self, key: str, value: str) -> bool:
        """تنظیم یک تنظیم"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO bot_settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value, datetime.datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"خطا در تنظیم: {e}")
            return False
    
    def is_bot_enabled(self) -> bool:
        """بررسی فعال بودن ربات"""
        return self.get_setting('bot_enabled') == '1'
    
    def set_bot_enabled(self, enabled: bool) -> bool:
        """تنظیم وضعیت ربات"""
        return self.set_setting('bot_enabled', '1' if enabled else '0')
    
    def enable_news_subscription(self, user_id: int) -> bool:
        """فعال کردن اشتراک اخبار برای کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET news_subscription_enabled = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
                logger.info(f"✅ اشتراک اخبار برای کاربر {user_id} فعال شد")
                return True
        except Exception as e:
            logger.error(f"خطا در فعال‌سازی اشتراک اخبار: {e}")
            return False
    
    def disable_news_subscription(self, user_id: int) -> bool:
        """غیرفعال کردن اشتراک اخبار برای کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET news_subscription_enabled = 0 WHERE user_id = ?', (user_id,))
                conn.commit()
                logger.info(f"❌ اشتراک اخبار برای کاربر {user_id} غیرفعال شد")
                return True
        except Exception as e:
            logger.error(f"خطا در غیرفعال‌سازی اشتراک اخبار: {e}")
            return False
    
    def is_news_subscribed(self, user_id: int) -> bool:
        """بررسی اشتراک اخبار کاربر"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT news_subscription_enabled FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return bool(result['news_subscription_enabled']) if result else False
        except Exception as e:
            logger.error(f"خطا در بررسی اشتراک اخبار: {e}")
            return False
    
    def get_news_subscribers(self) -> List[int]:
        """دریافت لیست کاربران مشترک اخبار (فعال و غیربلاک شده)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id FROM users 
                    WHERE news_subscription_enabled = 1 AND is_blocked = 0
                ''')
                return [row['user_id'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"خطا در دریافت لیست مشترکان اخبار: {e}")
            return []
    
    def get_recent_message_count(self, user_id: int, time_window: int) -> int:
        """دریافت تعداد پیام‌های اخیر کاربر در بازه زمانی مشخص"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # برای سادگی، از message_count استفاده می‌کنیم
                # در پیاده‌سازی کامل، نیاز به جدول پیام‌ها داریم
                cursor.execute(
                    'SELECT message_count FROM users WHERE user_id = ?',
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['message_count'] if result else 0
        except Exception as e:
            logger.error(f"خطا در دریافت تعداد پیام‌های اخیر: {e}")
            return 0
    
    def block_user_for_spam(self, user_id: int) -> Dict[str, Any]:
        """بلاک کردن کاربر به علت اسپم با مدت زمان مشخص"""
        try:
            # محاسبه زمان بلاک بر اساس سطح اسپم
            from datetime import datetime, timedelta
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # دریافت تعداد پیام‌های اخیر برای تعیین سطح اسپم
                cursor.execute(
                    'SELECT message_count FROM users WHERE user_id = ?',
                    (user_id,)
                )
                result = cursor.fetchone()
                message_count = result['message_count'] if result else 0
                
                # تعیین مدت زمان بلاک بر اساس تعداد پیام‌ها
                if message_count > 50:
                    # اسپم شدید - 1 روز
                    block_duration = 1
                    warning_level = "شدید"
                elif message_count > 30:
                    # اسپم متوسط - 12 ساعت
                    block_duration = 0.5  # 12 ساعت
                    warning_level = "متوسط"
                else:
                    # اسپم خفیف - 1 ساعت
                    block_duration = 1/24  # 1 ساعت
                    warning_level = "خفیف"
                
                block_until = datetime.now() + timedelta(hours=block_duration*24)
                
                cursor.execute('''
                    UPDATE users 
                    SET is_blocked = 1, block_until = ?
                    WHERE user_id = ?
                ''', (block_until, user_id))
                
                conn.commit()
                logger.info(f"کاربر {user_id} به علت اسپم تا {block_until} بلاک شد")
                
                return {
                    'success': True,
                    'warning_level': warning_level,
                    'block_until': block_until
                }
                
        except Exception as e:
            logger.error(f"خطا در بلاک کردن کاربر به علت اسپم: {e}")
            return {'success': False, 'warning_level': 'unknown'}
    
    def auto_unblock_expired_users(self) -> int:
        """آنبلاک خودکار کاربرانی که زمان بلاکشان تمام شده"""
        try:
            from datetime import datetime
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # آنبلاک کاربرانی که زمان بلاکشان تمام شده
                cursor.execute('''
                    UPDATE users 
                    SET is_blocked = 0, block_until = NULL
                    WHERE is_blocked = 1 
                    AND block_until IS NOT NULL 
                    AND block_until < ?
                ''', (datetime.now(),))
                
                unblocked_count = cursor.rowcount
                conn.commit()
                
                if unblocked_count > 0:
                    logger.info(f"✅ {unblocked_count} کاربر به صورت خودکار آنبلاک شدند")
                
                return unblocked_count
                
        except Exception as e:
            logger.error(f"خطا در آنبلاک خودکار کاربران: {e}")
            return 0

# نمونه سیستم لاگ سفارشی
class DatabaseLogger:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def log_user_action(self, user_id: int, action: str, message: str = ""):
        """لاگ عملیات کاربر"""
        self.db.add_log('USER_ACTION', f"{message} - Action: {action}", user_id, action)
    
    def log_admin_action(self, admin_id: int, action: str, target_user: int = None):
        """لاگ عملیات ادمین"""
        msg = f"Admin {admin_id} performed: {action}"
        if target_user:
            msg += f" on user {target_user}"
        self.db.add_log('ADMIN_ACTION', msg, admin_id, action)
    
    def log_system_event(self, event: str, details: str = ""):
        """لاگ رویدادهای سیستم"""
        self.db.add_log('SYSTEM', f"{event} - {details}", action=event)
