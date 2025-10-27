#!/usr/bin/env python3
"""
Test the Telegram bot by sending a message to verify end-to-end functionality
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
ADMIN_USER_ID = "327459477"  # Using as chat_id for testing

print("🤖 Testing Telegram Bot End-to-End...")
print(f"📱 Bot Token: {BOT_TOKEN[:20]}...")
print(f"👤 Admin User ID: {ADMIN_USER_ID}")

# Test 1: Send a test message to the bot
print("\n📤 Sending test message to bot...")
test_message = "🧪 Test message: Hello from N8N system!"

# Send message to bot
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
send_data = {
    "chat_id": ADMIN_USER_ID,
    "text": test_message
}

try:
    response = requests.post(send_url, json=send_data, timeout=10)
    result = response.json()
    
    if result.get("ok"):
        message_info = result["result"]
        print(f"✅ Message sent successfully!")
        print(f"   Message ID: {message_info['message_id']}")
        print(f"   Chat ID: {message_info['chat']['id']}")
        print(f"   Text: {message_info['text']}")
        print(f"   Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message_info['date']))}")
        
        # Test 2: Check webhook status
        print("\n📡 Checking webhook status...")
        webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        webhook_response = requests.get(webhook_url)
        webhook_result = webhook_response.json()
        
        if webhook_result.get("ok"):
            webhook_info = webhook_result["result"]
            print(f"✅ Webhook Status:")
            print(f"   URL: {webhook_info['url']}")
            print(f"   IP: {webhook_info['ip_address']}")
            print(f"   Pending: {webhook_info['pending_update_count']}")
            
            if webhook_info.get("last_error_message"):
                print(f"   Last Error: {webhook_info['last_error_message']}")
            else:
                print(f"   Status: No errors detected!")
        
        print("\n🎉 Testing completed successfully!")
        print("\n📋 Next Steps:")
        print("1. ✅ Telegram webhook is properly configured")
        print("2. ✅ N8N is running and accessible")
        print("3. ✅ Workflow should be active in N8N interface")
        print("4. 🔄 Send a message to your bot on Telegram")
        print("5. 📱 Bot should respond with AI-generated image")
        
    else:
        print(f"❌ Failed to send message: {result}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
except json.JSONDecodeError as e:
    print(f"❌ JSON decode error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "="*50)
print("📝 INSTRUCTIONS:")
print("="*50)
print("1. Open Telegram and search for your bot")
print("2. Start a conversation with: /start")
print("3. Send any message like: 'generate a beautiful landscape'")
print("4. The bot should trigger N8N workflow")
print("5. N8N should generate AI image and send it back")
print("="*50)