#!/usr/bin/env python3
import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # بررسی وجود ستون
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name='news_subscription_enabled'
    """)
    
    result = cursor.fetchone()
    
    if result:
        print("✅ ستون news_subscription_enabled در دیتابیس موجود است")
    else:
        print("❌ ستون news_subscription_enabled در دیتابیس موجود نیست")
        print("🔧 در حال اضافه کردن ستون...")
        
        # اضافه کردن ستون
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS news_subscription_enabled INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("✅ ستون با موفقیت اضافه شد")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ خطا: {e}")
