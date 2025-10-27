#!/usr/bin/env python3
"""
Check current webhook status to diagnose SSL issues
"""

import requests
import json

# Bot configuration
BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

def main():
    print("🔍 بررسی وضعیت فعلی وبهوک...")
    print("=" * 50)
    
    # Get webhook info
    webhook_info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(webhook_info_url)
        data = response.json()
        
        if data.get("ok"):
            info = data.get("result", {})
            
            print("📋 اطلاعات وبهوک:")
            print(f"  🌐 URL: {info.get('url', 'تنظیم نشده')}")
            print(f"  📡 IP آدرس: {info.get('ip_address', 'نامشخص')}")
            print(f"  ⏳ پیام‌های در صف: {info.get('pending_update_count', 0)}")
            print(f"  🔒 آخرین خطا: {info.get('last_error_message', 'هیچ')}")
            print(f"  ⏰ آخرین تاریخ خطا: {info.get('last_error_date', 'هیچ')}")
            print(f"  🔧 حداکثر اتصال: {info.get('max_connections', 'نامشخص')}")
            
            # Check if SSL issue exists
            current_url = info.get('url', '')
            current_ip = info.get('ip_address', '')
            
            print("\n🔍 تحلیل مشکل:")
            if current_ip and 'iqv2.onrender.com' not in current_url:
                print("❌ مشکل پیدا شد: وبهوک از آیپی استفاده می‌کند!")
                print(f"   🔸 وبهوک فعلی: {current_url}")
                print(f"   🔸 آیپی: {current_ip}")
                print("   ⚡ راه‌حل: تنظیم مجدد با دامین")
            elif 'iqv2.onrender.com' in current_url:
                print("✅ وبهوک با دامین تنظیم شده")
                if info.get('last_error_message'):
                    print("⚠️ اما هنوز خطا وجود داره")
                else:
                    print("✅ هیچ خطایی گزارش نشده")
            else:
                print("❓ وبهوک تنظیم نشده")
                
        else:
            print(f"❌ خطا در دریافت اطلاعات: {data.get('description')}")
            
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")

if __name__ == "__main__":
    main()