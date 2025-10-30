#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت ایجاد جدول AI usage tracking
این اسکریپت جدول و ویوهای لازم برای ردیابی مصرف توکن AI را ایجاد می‌کند
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

# تنظیمات logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_usage_tracking_table():
    """ایجاد جدول و ویوهای ردیابی مصرف AI"""
    
    # گرفتن DATABASE_URL از متغیر محیطی
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        return False
    
    # Parse database URL
    try:
        parsed = urlparse(database_url)
        connection_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'  # Required for most cloud databases
        }
    except Exception as e:
        logger.error(f"❌ Error parsing database URL: {e}")
        return False
    
    conn = None
    try:
        # اتصال به دیتابیس
        logger.info("🔗 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # SQL برای ایجاد جدول
        table_sql = """
        -- جدول ردیابی مصرف توکن AI
        CREATE TABLE IF NOT EXISTS ai_usage_tracking (
            id SERIAL PRIMARY KEY,
            provider VARCHAR(50) NOT NULL,
            user_id BIGINT,
            chat_id BIGINT,
            model VARCHAR(100),
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            rate_limit_info JSONB,
            cost_estimate DECIMAL(10, 6) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT NOW(),
            date DATE DEFAULT CURRENT_DATE
        );
        """
        
        # ایجاد ایندکس‌ها
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_provider ON ai_usage_tracking(provider);",
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_date ON ai_usage_tracking(date);",
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_user ON ai_usage_tracking(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_ai_usage_created_at ON ai_usage_tracking(created_at);"
        ]
        
        # ایجاد ویو آمار روزانه
        daily_view_sql = """
        CREATE OR REPLACE VIEW daily_ai_usage AS
        SELECT 
            provider,
            date,
            COUNT(*) as total_requests,
            SUM(total_tokens) as total_tokens_used,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(cost_estimate) as total_cost,
            AVG(total_tokens) as avg_tokens_per_request
        FROM ai_usage_tracking
        GROUP BY provider, date
        ORDER BY date DESC, provider;
        """
        
        # ایجاد ویو آمار کلی
        provider_stats_sql = """
        CREATE OR REPLACE VIEW provider_ai_stats AS
        SELECT 
            provider,
            COUNT(*) as total_requests,
            SUM(total_tokens) as total_tokens_used,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(cost_estimate) as total_cost,
            MIN(created_at) as first_usage,
            MAX(created_at) as last_usage,
            AVG(total_tokens) as avg_tokens_per_request
        FROM ai_usage_tracking
        GROUP BY provider
        ORDER BY total_tokens_used DESC;
        """
        
        # اجرای SQL ها
        logger.info("📋 Creating ai_usage_tracking table...")
        cursor.execute(table_sql)
        
        logger.info("🗂️ Creating indexes...")
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        
        logger.info("👁️ Creating daily_ai_usage view...")
        cursor.execute(daily_view_sql)
        
        logger.info("📊 Creating provider_ai_stats view...")
        cursor.execute(provider_stats_sql)
        
        # Commit changes
        conn.commit()
        
        # بررسی ایجاد جدول
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'ai_usage_tracking'
        """)
        
        if cursor.fetchone():
            logger.info("✅ Table 'ai_usage_tracking' created successfully!")
        else:
            logger.error("❌ Failed to create table 'ai_usage_tracking'")
            return False
        
        # بررسی ایجاد ویوها
        cursor.execute("""
            SELECT table_name FROM information_schema.views 
            WHERE table_name IN ('daily_ai_usage', 'provider_ai_stats')
        """)
        
        views = [row[0] for row in cursor.fetchall()]
        if 'daily_ai_usage' in views:
            logger.info("✅ View 'daily_ai_usage' created successfully!")
        else:
            logger.warning("⚠️ View 'daily_ai_usage' not found, but SQL executed successfully")
        if 'provider_ai_stats' in views:
            logger.info("✅ View 'provider_ai_stats' created successfully!")
        else:
            logger.warning("⚠️ View 'provider_ai_stats' not found, but SQL executed successfully")
        
        cursor.close()
        
        logger.info("🎉 AI usage tracking database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating usage tracking tables: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()
            logger.info("🔒 Database connection closed")

def test_database_connection():
    """تست اتصال به دیتابیس"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
        
        parsed = urlparse(database_url)
        connection_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'
        }
        
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # تست ساده
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"✅ Database connection successful! PostgreSQL version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AI Usage Tracking Database Setup")
    print("=" * 50)
    
    # تست اتصال
    print("\n1️⃣ Testing database connection...")
    if not test_database_connection():
        print("❌ Database connection failed. Exiting.")
        exit(1)
    
    # ایجاد جدول
    print("\n2️⃣ Creating usage tracking tables...")
    if create_usage_tracking_table():
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 You can now test the admin panel '💎 گزارش توکن AI' button")
    else:
        print("\n❌ Database setup failed. Please check the logs above.")