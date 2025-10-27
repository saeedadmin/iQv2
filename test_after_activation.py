#!/usr/bin/env python3
"""
Test webhook activation - Run this AFTER you activate the workflow in N8N
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WEBHOOK_URL = "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook"
N8N_BASE_URL = "https://iqv2.onrender.com"

print("🧪 WORKFLOW ACTIVATION TEST")
print("=" * 50)
print("⚠️ IMPORTANT: Run this AFTER you've activated the workflow in N8N!")
print("=" * 50)

# Test 1: Check webhook status
print("\n1. 📡 Checking Webhook Status...")
webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(webhook_url)
    result = response.json()
    
    if result.get("ok"):
        info = result["result"]
        print(f"   🔗 Webhook URL: {info['url']}")
        print(f"   ⏳ Pending Updates: {info['pending_update_count']}")
        
        if info.get("last_error_message"):
            print(f"   ❌ Last Error: {info['last_error_message']}")
        else:
            print(f"   ✅ No errors")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Test webhook endpoint
print(f"\n2. 🔄 Testing Webhook Endpoint...")
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Test message for activation"
    }
}

try:
    response = requests.post(WEBHOOK_URL, json=test_data, timeout=10)
    status = response.status_code
    
    print(f"   📊 Response Code: {status}")
    
    if status == 200:
        print(f"   ✅ SUCCESS! Workflow is ACTIVE and working!")
        print(f"   🎉 Webhook accepted the request")
        
        # Wait a moment and check again for pending updates
        print(f"\n   ⏳ Waiting 5 seconds to check pending updates...")
        time.sleep(5)
        
        # Check webhook info again
        response2 = requests.get(webhook_url)
        result2 = response2.json()
        if result2.get("ok"):
            pending = result2["result"]["pending_update_count"]
            if pending == 0:
                print(f"   ✅ Perfect! Pending updates: {pending}")
            else:
                print(f"   ⚠️ Pending updates still: {pending}")
                
    elif status == 403:
        print(f"   ❌ FAILED! Workflow is still INACTIVE")
        print(f"   🔧 Go back to N8N interface and make sure workflow is ACTIVE")
        print(f"   📍 URL: {N8N_BASE_URL}/workflows/ff17baeb-3182-41c4-b60a-e6159b02023b")
    else:
        print(f"   ⚠️ Unexpected status: {status}")
        print(f"   📝 Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print(f"   ⏰ Timeout - Server not responding")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Send actual test message to bot
print(f"\n3. 📱 Sending Test Message to Bot...")
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
test_message = {
    "chat_id": "327459477",
    "text": "🧪 Test message - if you receive this, bot is working!"
}

try:
    response = requests.post(send_url, json=test_message, timeout=5)
    result = response.json()
    
    if result.get("ok"):
        print(f"   ✅ Test message sent successfully")
        print(f"   📱 Message ID: {result['result']['message_id']}")
    else:
        print(f"   ❌ Failed to send test message: {result}")
        
except Exception as e:
    print(f"   ❌ Error sending message: {e}")

print("\n" + "=" * 50)
print("📋 SUMMARY")
print("=" * 50)

# Wait and do final check
print(f"\n⏳ Final webhook status check...")
time.sleep(3)

try:
    final_response = requests.get(webhook_url)
    final_result = final_response.json()
    
    if final_result.get("ok"):
        final_info = final_result["result"]
        print(f"\n🎯 FINAL STATUS:")
        print(f"   🔗 Webhook: {final_info['url']}")
        print(f"   ⏳ Pending: {final_info['pending_update_count']}")
        
        if final_info.get("last_error_message"):
            print(f"   ❌ Error: {final_info['last_error_message']}")
        else:
            print(f"   ✅ No errors detected!")
            
        if final_info['pending_update_count'] == 0:
            print(f"\n🎉 PERFECT! System is working correctly!")
            print(f"📱 Ready to use - send any message to your bot")
        else:
            print(f"\n⚠️ Still has pending updates - may need retry")
    
except Exception as e:
    print(f"   ❌ Final check error: {e}")

print(f"\n🚀 NEXT STEPS:")
print(f"1. ✅ If webhook shows 200: Bot is working!")
print(f"2. 📱 Send message: 'generate a beautiful landscape'")
print(f"3. 🖼️ Wait for AI image generation")
print(f"4. 🎉 Enjoy your working bot!")
print("=" * 50)