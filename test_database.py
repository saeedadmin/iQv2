#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست سریع جدول AI usage tracking
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def test_usage_tables():
    """تست جدول‌های AI usage tracking"""
    
    # گرفتن DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return False
    
    try:
        # اتصال
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 Testing AI usage tracking tables...")
        
        # 1. بررسی وجود جدول
        cursor.execute("""
            SELECT COUNT(*) as table_exists 
            FROM information_schema.tables 
            WHERE table_name = 'ai_usage_tracking'
        """)
        result = cursor.fetchone()
        if result['table_exists'] > 0:
            print("✅ Table 'ai_usage_tracking' exists")
        else:
            print("❌ Table 'ai_usage_tracking' not found")
            return False
        
        # 2. تست افزودن رکورد نمونه
        print("🧪 Testing insert...")
        cursor.execute("""
            INSERT INTO ai_usage_tracking (provider, user_id, chat_id, model, prompt_tokens, completion_tokens, total_tokens, cost_estimate)
            VALUES ('test', 123456789, 987654321, 'test-model', 100, 200, 300, 0.005)
        """)
        conn.commit()
        print("✅ Insert test successful")
        
        # 3. تست ویوها
        print("👁️ Testing views...")
        
        # تست daily_ai_usage view
        cursor.execute("SELECT * FROM daily_ai_usage LIMIT 5")
        daily_results = cursor.fetchall()
        print(f"✅ View 'daily_ai_usage' working - Found {len(daily_results)} daily records")
        
        # تست provider_ai_stats view  
        cursor.execute("SELECT * FROM provider_ai_stats LIMIT 5")
        provider_results = cursor.fetchall()
        print(f"✅ View 'provider_ai_stats' working - Found {len(provider_results)} provider records")
        
        # 4. حذف رکورد تست
        cursor.execute("DELETE FROM ai_usage_tracking WHERE provider = 'test'")
        conn.commit()
        print("🧹 Test record cleaned up")
        
        # 5. بررسی ساختار جدول
        print("\n📋 Table structure:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'ai_usage_tracking'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  - {col['column_name']}: {col['data_type']} {nullable} {default}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 All tests passed! Database setup is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_usage_tables()