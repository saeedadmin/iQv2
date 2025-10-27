#!/usr/bin/env python3
"""
Quick test after Telegram Trigger activation
"""

import requests
import json
import time

# Configuration
BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

def test_workflow_response():
    """Test if workflow now responds with 200"""
    print("🔍 تست سریع وضعیت ورکفلو...")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json={"test": "activation_verification"},
            timeout=10
        )
        
        status_code = response.status_code
        
        if status_code == 200:
            print("🎉 موفقیت! ورکفلو فعاله و آماده!")
            print("✅ کد پاسخ: 200")
            print("✅ حالا ربات باید جواب بده")
            return True
        elif status_code == 403:
            print("❌ هنوز 403 می‌گیرید - ورکفلو فعال نشده")
            print("🔧 لطفاً مراحل فعال‌سازی رو دوباره انجام بدید")
            return False
        else:
            print(f"❓ کد پاسخ غیرمعمول: {status_code}")
            return False
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

def main():
    print("⚡ تست سریع بعد از فعال‌سازی")
    print("=" * 40)
    
    success = test_workflow_response()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 همه چیز درسته! حالا تست کنید:")
        print("   📱 به ربات @your_bot_name پیام بدید")
        print("   🤖 باید عکس AI تولید کنه")
    else:
        print("⚠️ ورکفلو هنوز فعال نیست")
        print("📝 لطفاً راهنمای DETAILED_TELEGRAM_TRIGGER_GUIDE.md رو دنبال کنید")

if __name__ == "__main__":
    main()