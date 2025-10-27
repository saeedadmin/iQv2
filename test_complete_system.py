#!/usr/bin/env python3
"""
Test both webhook registration and workflow activation status
"""

import requests
import json
import time

# Configuration
BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

def test_webhook_registration():
    """Test webhook registration status"""
    print("🔍 بررسی وضعیت وبهوک...")
    
    webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_info_url)
        data = response.json()
        
        if data.get("ok"):
            info = data.get("result", {})
            current_url = info.get('url', '')
            pending = info.get('pending_update_count', 0)
            error = info.get('last_error_message', 'هیچ')
            
            if 'iqv2.onrender.com' in current_url and pending == 0:
                print("✅ وبهوک درست تنظیم شده (دامین، بدون خطا)")
                return True
            else:
                print(f"❌ مشکل وبهوک: URL={current_url}, پیام‌های در صف={pending}, خطا={error}")
                return False
        else:
            print(f"❌ خطا در بررسی وبهوک: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطا در تست وبهوک: {e}")
        return False

def test_workflow_activation():
    """Test if workflow is properly activated for webhooks"""
    print("🔧 تست فعال‌سازی ورکفلو...")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Test the webhook endpoint
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json={"test": "activation_check"},
            timeout=10
        )
        
        status_code = response.status_code
        
        print(f"📊 کد پاسخ: {status_code}")
        
        if status_code == 200:
            print("✅ ورکفلو فعال و آماده دریافت پیام!")
            return True
        elif status_code == 403:
            print("❌ ورکفلو هنوز فعال نیست (خطای 403)")
            print("🔧 راه‌حل: در N8N باید تلگرام تریگر رو فعال کنید")
            print("📝 لطفاً این مراحل رو دنبال کنید:")
            print("   1. به https://iqv2.onrender.com برید")
            print("   2. ورکفلو رو باز کنید: workflows/ff17baeb-3182-41c4-b60a-e6159b02023b")
            print("   3. روی گره Telegram Trigger کلیک کنید")
            print("   4. دکمه فعال‌سازی (toggle) رو پیدا کنید")
            print("   5. روی دکمه کلیک کنید تا سبز بشه")
            return False
        elif status_code == 404:
            print("❌ وبهوک پیدا نشد (خطای 404)")
            print("🔧 راه‌حل: مجدداً وبهوک رو تنظیم کنید")
            return False
        else:
            print(f"❓ کد پاسخ غیرمعمول: {status_code}")
            print(f"محتوای پاسخ: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ تایم‌اوت - وبهوک پاسخ نمی‌ده")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 خطای اتصال - مشکل سرور")
        return False
    except Exception as e:
        print(f"❌ خطا در تست ورکفلو: {e}")
        return False

def test_telegram_message():
    """Send test message to bot"""
    print("📱 ارسال پیام تست به ربات...")
    
    send_message_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": "327459477",
        "text": "🤖 تست سیستم:\n\nاین پیام برای تست فعال‌سازی ورکفلو ارسال شده.\nاگر ورکفلو فعال باشه، باید عکسی از AI تولید شه.\n\n⏰ زمان: " + time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        response = requests.post(send_message_url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ پیام تست ارسال شد")
            message_id = result.get("result", {}).get("message_id")
            print(f"🆔 آیدی پیام: {message_id}")
            return True
        else:
            print(f"❌ خطا در ارسال پیام: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطا در ارسال پیام: {e}")
        return False

def main():
    print("🧪 تست جامع وضعیت سیستم...")
    print("=" * 50)
    
    # Test 1: Webhook registration
    webhook_ok = test_webhook_registration()
    
    print()
    
    # Test 2: Workflow activation
    workflow_ok = test_workflow_activation()
    
    print()
    
    # Test 3: Send test message (only if webhook is ok)
    if webhook_ok:
        message_ok = test_telegram_message()
    else:
        message_ok = False
    
    print()
    print("=" * 50)
    print("📊 خلاصه نتایج:")
    print(f"   🌐 وبهوک: {'✅ درست' if webhook_ok else '❌ مشکل'}")
    print(f"   🔧 ورکفلو: {'✅ فعال' if workflow_ok else '❌ غیرفعال'}")
    print(f"   📱 پیام تست: {'✅ ارسال شد' if message_ok else '❌ ارسال نشد'}")
    
    print("\n🎯 اقدامات بعدی:")
    if not workflow_ok:
        print("⚠️ مهم‌ترین مشکل: ورکفلو باید در N8N فعال بشه")
        print("📝 لطفاً مراحل فعال‌سازی رو در راهنمای قبلی دنبال کنید")
    elif webhook_ok and workflow_ok and not message_ok:
        print("⚠️ مشکل در ارسال پیام - لطفاً تست کنید")
    elif webhook_ok and workflow_ok:
        print("🎉 همه چیز درسته! ربات باید کار کنه")
    else:
        print("⚠️ مشکل در وبهوک - نیاز به بررسی بیشتر")

if __name__ == "__main__":
    main()