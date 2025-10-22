#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Migration Script: اضافه کردن فیلد news_subscription_enabled به جدول users (برای PostgreSQL)
نویسنده: MiniMax Agent
تاریخ: 2025-10-22
"""

import psycopg2
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database_postgres():
    """اضافه کردن فیلد news_subscription_enabled به دیتابیس PostgreSQL"""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL تنظیم نشده است")
            return False
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # بررسی وجود فیلد
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='news_subscription_enabled'
        """)
        
        result = cursor.fetchone()
        
        if not result:
            logger.info("🔧 اضافه کردن فیلد news_subscription_enabled به جدول users...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN news_subscription_enabled INTEGER DEFAULT 0
            """)
            conn.commit()
            logger.info("✅ فیلد news_subscription_enabled با موفقیت اضافه شد")
        else:
            logger.info("✅ فیلد news_subscription_enabled قبلاً وجود دارد")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در migration: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 شروع migration برای PostgreSQL...")
    success = migrate_database_postgres()
    if success:
        logger.info("🎉 Migration با موفقیت کامل شد!")
    else:
        logger.error("❌ Migration ناموفق بود")
