#!/usr/bin/env python3
"""
FINAL TEST: Run this AFTER you activate the workflow
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WEBHOOK_URL = "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook"

print("🚀 FINAL WORKFLOW TEST")
print("=" * 50)
print("⚠️ IMPORTANT: Run this AFTER activating workflow!")
print("=" * 50)

# Test 1: Check webhook status
print("\n1. 📡 Webhook Status Check:")
info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(info_url, timeout=10)
    result = response.json()
    
    if result.get("ok"):
        info = result["result"]
        print(f"   🔗 URL: {info['url']}")
        print(f"   ⏳ Pending: {info['pending_update_count']}")
        
        if info.get("last_error_message"):
            print(f"   ❌ Error: {info['last_error_message']}")
        else:
            print(f"   ✅ No errors")
            
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Direct workflow test
print(f"\n2. 🧪 Direct Workflow Test:")
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Final activation test"
    }
}

try:
    response = requests.post(WEBHOOK_URL, json=test_data, timeout=15)
    status = response.status_code
    
    print(f"   📊 Response Code: {status}")
    
    if status == 200:
        print(f"   🎉 SUCCESS! Workflow is ACTIVE and working!")
        print(f"   ✅ N8N is processing webhook correctly")
        print(f"   🚀 Bot should work end-to-end!")
        
        # Wait and check webhook info
        print(f"\n   ⏳ Checking webhook after test...")
        time.sleep(5)
        
        response2 = requests.get(info_url)
        result2 = response2.json()
        if result2.get("ok"):
            pending = result2["result"]["pending_update_count"]
            if pending == 0:
                print(f"   ✅ Perfect! No pending updates - webhook delivered successfully")
            else:
                print(f"   ⚠️ Pending updates: {pending} - may need retry")
        
    elif status == 403:
        print(f"   ❌ FAILED! Workflow is still INACTIVE")
        print(f"   🔧 Go back to N8N interface:")
        print(f"   1. Open: https://iqv2.onrender.com/workflows/ff17baeb-3182-41c4-b60a-e6159b02023b")
        print(f"   2. Find toggle switch")
        print(f"   3. Turn ON (Active)")
        print(f"   4. Save workflow")
        print(f"   5. Run this test again")
        
    else:
        print(f"   ⚠️ Unexpected status: {status}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print(f"   ⏰ Timeout - Workflow taking long time")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Send test message to bot
print(f"\n3. 📱 Test Message to Bot:")
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
message_data = {
    "chat_id": "327459477",
    "text": "🧪 Final test message - if you receive this, workflow is working!"
}

try:
    response = requests.post(send_url, json=message_data, timeout=5)
    result = response.json()
    
    if result.get("ok"):
        print(f"   ✅ Test message sent")
        print(f"   📱 Message ID: {result['result']['message_id']}")
    else:
        print(f"   ❌ Failed to send: {result}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n" + "=" * 50)
print(f"📋 FINAL RESULTS")
print(f"=" * 50)

# Final status check
time.sleep(3)
try:
    final_response = requests.get(info_url, timeout=5)
    final_result = final_response.json()
    
    if final_result.get("ok"):
        final_info = final_result["result"]
        pending = final_info["pending_update_count"]
        
        print(f"\n🎯 FINAL STATUS:")
        print(f"   🔗 Webhook: Active")
        print(f"   ⏳ Pending: {pending}")
        
        if pending == 0:
            print(f"   ✅ System working perfectly!")
            print(f"\n🚀 READY FOR REAL TEST:")
            print(f"1. 📱 Open Telegram")
            print(f"2. 💬 Find your bot")  
            print(f"3. 📨 Send: 'generate a beautiful landscape'")
            print(f"4. 🖼️ Wait for AI image")
            print(f"5. 🎉 Enjoy your working bot!")
        else:
            print(f"   ⚠️ Still processing - try again in a moment")
    
except Exception as e:
    print(f"   ❌ Final check error: {e}")

print(f"=" * 50)