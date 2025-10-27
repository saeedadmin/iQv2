#!/usr/bin/env python3
"""
Force webhook re-registration with domain to fix SSL issues
This script fixes the persistent webhook URL issue
"""

import requests
import time
import json

# Bot configuration
BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

def delete_webhook():
    """Delete current webhook and clear pending updates"""
    print("🗑️ حذف وبهوک فعلی...")
    
    delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    data = {"drop_pending_updates": True}
    
    try:
        response = requests.post(delete_url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ وبهوک حذف شد و پیام‌های در صف پاک شد")
            return True
        else:
            print(f"❌ خطا در حذف وبهوک: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def set_webhook_domain():
    """Register webhook with domain URL"""
    print("🔗 تنظیم وبهوک با دامین...")
    
    set_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {
        "url": WEBHOOK_URL,
        "max_connections": 40,
        "allowed_updates": ["message"]
    }
    
    try:
        response = requests.post(set_url, json=data)
        result = response.json()
        
        if result.get("ok"):
            print("✅ وبهوک با دامین تنظیم شد!")
            return True
        else:
            print(f"❌ خطا در تنظیم وبهوک: {result.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def wait_and_check():
    """Wait a bit and check webhook status"""
    print("⏳ صبر کردن برای تثبیت...")
    time.sleep(5)
    
    print("🔍 بررسی وضعیت نهایی...")
    
    webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_info_url)
        data = response.json()
        
        if data.get("ok"):
            info = data.get("result", {})
            current_url = info.get('url', '')
            pending = info.get('pending_update_count', 0)
            error = info.get('last_error_message', 'هیچ')
            
            print(f"📋 نتیجه نهایی:")
            print(f"   🌐 وبهوک: {current_url}")
            print(f"   ⏳ پیام‌های در صف: {pending}")
            print(f"   🔒 خطاها: {error}")
            
            if 'iqv2.onrender.com' in current_url and pending == 0:
                print("🎉 موفقیت! وبهوک درست تنظیم شد")
                return True
            else:
                print("⚠️ هنوز مشکل وجود داره")
                return False
        else:
            print(f"❌ خطا در بررسی وضعیت: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ خطا در بررسی: {e}")
        return False

def main():
    print("🔧 شروع رفع مشکل وبهوک...")
    print("=" * 50)
    
    # Step 1: Delete current webhook
    if not delete_webhook():
        print("❌ متوقف شد - خطا در حذف وبهوک")
        return
    
    time.sleep(2)
    
    # Step 2: Set webhook with domain
    if not set_webhook_domain():
        print("❌ متوقف شد - خطا در تنظیم وبهوک")
        return
    
    # Step 3: Wait and verify
    if wait_and_check():
        print("\n✅ وبهوک درست شد! حالا تست کنید:")
        print("   📱 به ربات تلگرام پیام بفرستید")
        print("   🔍 اگه باز خطا داشتید، لطفاً اطلاع بدید")
    else:
        print("\n⚠️ مشکل هنوز برطرف نشده. نیاز به بررسی بیشتر")

if __name__ == "__main__":
    main()