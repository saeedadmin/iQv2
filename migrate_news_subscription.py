#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Migration Script: اضافه کردن فیلد news_subscription_enabled به جدول users
نویسنده: MiniMax Agent
تاریخ: 2025-10-22
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database(db_path="bot_database.db"):
    """اضافه کردن فیلد news_subscription_enabled به دیتابیس"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # بررسی وجود فیلد
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'news_subscription_enabled' not in columns:
            logger.info("🔧 اضافه کردن فیلد news_subscription_enabled به جدول users...")
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN news_subscription_enabled INTEGER DEFAULT 0
            ''')
            conn.commit()
            logger.info("✅ فیلد news_subscription_enabled با موفقیت اضافه شد")
        else:
            logger.info("✅ فیلد news_subscription_enabled قبلاً وجود دارد")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در migration: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 شروع migration...")
    success = migrate_database()
    if success:
        logger.info("🎉 Migration با موفقیت کامل شد!")
    else:
        logger.error("❌ Migration ناموفق بود")
