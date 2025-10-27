#!/usr/bin/env python3
"""
Direct webhook registration with Telegram API
"""

import requests
import json
import time

def register_telegram_webhook():
    """Register webhook directly with Telegram API"""
    
    bot_token = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
    webhook_url = "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook"
    
    print("🤖 Registering Telegram Webhook...")
    print(f"Bot Token: {bot_token[:20]}...")
    print(f"Webhook URL: {webhook_url}")
    print("")
    
    # Telegram Bot API endpoint
    telegram_api = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    # Data to send
    data = {
        "url": webhook_url,
        "max_connections": 40,
        "allowed_updates": ["message", "edited_message", "callback_query"]
    }
    
    try:
        print("📤 Sending webhook registration request...")
        response = requests.post(telegram_api, json=data, timeout=30)
        
        print(f"🔍 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ SUCCESS! Webhook registered successfully!")
                print(f"📍 Webhook URL: {result['result']['url']}")
                if 'ip_address' in result['result']:
                    print(f"🌐 Registered IP: {result['result']['ip_address']}")
                print(f"📊 Description: {result['result']['description']}")
            else:
                print(f"❌ Telegram API Error: {result}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Also try to get current webhook info
    print("\n" + "="*50)
    print("📋 Current Webhook Status")
    print("="*50)
    
    try:
        get_webhook_info = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        info_response = requests.get(get_webhook_info, timeout=10)
        
        if info_response.status_code == 200:
            info_result = info_response.json()
            if info_result.get("ok"):
                webhook_info = info_result["result"]
                print(f"🔗 Current Webhook: {webhook_info.get('url', 'None')}")
                print(f"📱 IP Address: {webhook_info.get('ip_address', 'None')}")
                print(f"📊 Max Connections: {webhook_info.get('max_connections', 'None')}")
                print(f"🕒 Last Error Date: {webhook_info.get('last_error_date', 'None')}")
                if webhook_info.get('last_error_message'):
                    print(f"❌ Last Error: {webhook_info['last_error_message']}")
            else:
                print(f"❌ Info API Error: {info_result}")
        else:
            print(f"❌ Info HTTP Error {info_response.status_code}")
            
    except Exception as e:
        print(f"❌ Info Exception: {e}")

if __name__ == "__main__":
    register_telegram_webhook()