#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست کامل سیستم AI usage tracking
این اسکریپت تمام اجزای سیستم ردیابی مصرف AI را تست می‌کند
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def test_complete_ai_usage_system():
    """تست کامل سیستم AI usage tracking"""
    
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
        
        print("🤖 Testing Complete AI Usage Tracking System")
        print("=" * 60)
        
        # 1. تست جدول
        print("\n1️⃣ Testing ai_usage_tracking table...")
        cursor.execute("""
            SELECT COUNT(*) as count FROM information_schema.tables 
            WHERE table_name = 'ai_usage_tracking'
        """)
        if cursor.fetchone()['count'] > 0:
            print("✅ Table 'ai_usage_tracking' exists")
        else:
            print("❌ Table 'ai_usage_tracking' not found")
            return False
        
        # 2. تست ساختار جدول
        print("\n2️⃣ Testing table structure...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'ai_usage_tracking'
            ORDER BY ordinal_position
        """)
        
        columns = [row['column_name'] for row in cursor.fetchall()]
        expected_columns = [
            'id', 'provider', 'user_id', 'chat_id', 'model',
            'prompt_tokens', 'completion_tokens', 'total_tokens',
            'rate_limit_info', 'cost_estimate', 'created_at', 'date'
        ]
        
        missing_columns = set(expected_columns) - set(columns)
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All expected columns exist")
        
        # 3. تست ایندکس‌ها
        print("\n3️⃣ Testing indexes...")
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'ai_usage_tracking'
        """)
        
        indexes = [row['indexname'] for row in cursor.fetchall()]
        print(f"✅ Found {len(indexes)} indexes: {indexes}")
        
        # 4. تست ویوها
        print("\n4️⃣ Testing views...")
        
        # تست daily_ai_usage view
        cursor.execute("SELECT * FROM daily_ai_usage LIMIT 1")
        daily_result = cursor.fetchall()
        print(f"✅ View 'daily_ai_usage' working - {len(daily_result)} records")
        
        # تست provider_ai_stats view
        cursor.execute("SELECT * FROM provider_ai_stats LIMIT 1")
        provider_result = cursor.fetchall()
        print(f"✅ View 'provider_ai_stats' working - {len(provider_result)} records")
        
        # 5. تست درج نمونه داده
        print("\n5️⃣ Testing data insertion...")
        
        test_data = [
            ('groq', 123456789, 987654321, 'llama-3.1-70b-versatile', 150, 200, 350, 0.007),
            ('cerebras', 123456789, 987654321, 'llama-3.1-70b', 120, 180, 300, 0.006),
            ('gemini', 123456789, 987654321, 'gemini-1.5-pro', 100, 150, 250, 0.005),
            ('cohere', 123456789, 987654321, 'command-r-plus', 80, 120, 200, 0.004)
        ]
        
        for provider, user_id, chat_id, model, prompt_tokens, completion_tokens, total_tokens, cost in test_data:
            cursor.execute("""
                INSERT INTO ai_usage_tracking 
                (provider, user_id, chat_id, model, prompt_tokens, completion_tokens, total_tokens, cost_estimate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (provider, user_id, chat_id, model, prompt_tokens, completion_tokens, total_tokens, cost))
        
        conn.commit()
        print(f"✅ Inserted {len(test_data)} test records")
        
        # 6. تست ویوها با داده
        print("\n6️⃣ Testing views with data...")
        
        cursor.execute("SELECT * FROM daily_ai_usage ORDER BY date DESC")
        daily_data = cursor.fetchall()
        print(f"📊 Daily usage view - {len(daily_data)} rows")
        if daily_data:
            row = daily_data[0]
            print(f"   Provider: {row['provider']}, Date: {row['date']}, Requests: {row['total_requests']}")
        
        cursor.execute("SELECT * FROM provider_ai_stats ORDER BY total_tokens_used DESC")
        provider_data = cursor.fetchall()
        print(f"📊 Provider stats view - {len(provider_data)} rows")
        if provider_data:
            row = provider_data[0]
            print(f"   Provider: {row['provider']}, Total tokens: {row['total_tokens_used']}")
        
        # 7. تست JSONB field
        print("\n7️⃣ Testing JSONB rate_limit_info field...")
        
        # اضافه کردن یک رکورد با rate_limit_info
        cursor.execute("""
            INSERT INTO ai_usage_tracking 
            (provider, user_id, model, total_tokens, rate_limit_info)
            VALUES ('cerebras', 999888777, 'llama-3.1-70b', 100, '{"tokens_remaining_minute": 50000, "tokens_limit_minute": 100000}')
        """)
        conn.commit()
        print("✅ JSONB rate_limit_info field working")
        
        # 8. تست آمار
        print("\n8️⃣ Testing statistics...")
        
        # تعداد کل رکوردها
        cursor.execute("SELECT COUNT(*) as total FROM ai_usage_tracking")
        total_records = cursor.fetchone()['total']
        print(f"📈 Total records: {total_records}")
        
        # مجموع توکن‌ها
        cursor.execute("SELECT SUM(total_tokens) as total_tokens FROM ai_usage_tracking")
        total_tokens = cursor.fetchone()['total_tokens']
        print(f"📈 Total tokens used: {total_tokens:,}")
        
        # بر اساس provider
        cursor.execute("""
            SELECT provider, COUNT(*) as count, SUM(total_tokens) as tokens 
            FROM ai_usage_tracking 
            GROUP BY provider
            ORDER BY tokens DESC
        """)
        
        for row in cursor.fetchall():
            print(f"   {row['provider']}: {row['count']} requests, {row['tokens']:,} tokens")
        
        # 9. پاک کردن تست داده
        print("\n9️⃣ Cleaning up test data...")
        cursor.execute("DELETE FROM ai_usage_tracking WHERE model LIKE 'llama-%' OR model LIKE 'gemini-%' OR model LIKE 'command-%'")
        conn.commit()
        print("✅ Test data cleaned up")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 All tests passed! AI Usage Tracking System is fully functional!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_system_summary():
    """نمایش خلاصه سیستم"""
    print("\n📋 AI Usage Tracking System Summary")
    print("=" * 50)
    print("✅ Database table: ai_usage_tracking")
    print("✅ Views: daily_ai_usage, provider_ai_stats")  
    print("✅ Indexes: optimized for performance")
    print("✅ Features: token tracking, cost estimation, rate limit monitoring")
    print("✅ Providers: Groq, Cerebras, Gemini, Cohere")
    print("\n🔄 Ready for admin panel testing!")

if __name__ == "__main__":
    print("🚀 Starting AI Usage Tracking System Test")
    
    if test_complete_ai_usage_system():
        show_system_summary()
    else:
        print("\n❌ System test failed. Please check the errors above.")