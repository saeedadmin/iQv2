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
                        is_admin INTEGER DEFAULT 0,
                        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0
                    )
                ''')
                
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
                
        except Exception as e:
            logger.error(f"خطا در مقداردهی دیتابیس: {e}")
    
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
