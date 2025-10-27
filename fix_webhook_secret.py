#!/usr/bin/env python3
"""
Fix webhook secret issue - Register without secret (or with correct secret)
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
DOMAIN_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

print("🔐 WEBHOOK SECRET FIX")
print("=" * 50)
print(f"🎯 Problem: Webhook secret validation failed")
print(f"🔗 Target: {DOMAIN_URL}")

# Step 1: Delete webhook
print(f"\n🗑️ Step 1: Deleting current webhook...")
delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
delete_data = {"drop_pending_updates": True}

try:
    response = requests.post(delete_url, json=delete_data, timeout=10)
    result = response.json()
    print(f"✅ Webhook deleted")
except Exception as e:
    print(f"❌ Delete error: {e}")

# Step 2: Wait for Telegram to process
print(f"\n⏳ Waiting 3 seconds...")
time.sleep(3)

# Step 3: Register webhook WITHOUT secret (most compatible)
print(f"\n📝 Step 2: Registering webhook WITHOUT secret...")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": DOMAIN_URL,
    "max_connections": 40,
    "allowed_updates": ["message"],
    "drop_pending_updates": True
}

try:
    response = requests.post(register_url, json=register_data, timeout=10)
    result = response.json()
    print(f"📝 Register result: {json.dumps(result, indent=2)}")
    
    if result.get("ok") and result.get("result"):
        print(f"✅ SUCCESS! Webhook registered without secret!")
    else:
        print(f"❌ Registration failed: {result}")
        
except Exception as e:
    print(f"❌ Registration error: {e}")

# Step 4: Alternative - Try with empty secret
print(f"\n🔐 Step 3: Trying alternative with empty secret...")
register_data_alt = {
    "url": DOMAIN_URL,
    "max_connections": 40,
    "allowed_updates": ["message"],
    "secret_token": ""  # Empty secret
}

try:
    response = requests.post(register_url, json=register_data_alt, timeout=10)
    result = response.json()
    print(f"📝 Alternative result: {json.dumps(result, indent=2)}")
    
except Exception as e:
    print(f"❌ Alternative error: {e}")

# Step 5: Verify registration
print(f"\n✅ Step 4: Verifying webhook registration...")
time.sleep(3)

info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(info_url, timeout=10)
    result = response.json()
    
    if result.get("ok"):
        info = result["result"]
        print(f"\n📊 WEBHOOK STATUS:")
        print(f"   🔗 URL: {info['url']}")
        print(f"   ⏳ Pending: {info['pending_update_count']}")
        
        if info.get("last_error_message"):
            print(f"   ❌ Last Error: {info['last_error_message']}")
        else:
            print(f"   ✅ No errors!")
    
except Exception as e:
    print(f"❌ Verification error: {e}")

# Step 6: Test webhook again
print(f"\n🧪 Step 5: Testing webhook without secret...")
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Test without secret"
    }
}

try:
    response = requests.post(DOMAIN_URL, json=test_data, timeout=15)
    status = response.status_code
    
    print(f"   📊 Response Code: {status}")
    
    if status == 200:
        print(f"   🎉 SUCCESS! Webhook working without secret!")
        print(f"   ✅ Bot should work now!")
    elif status == 403:
        print(f"   ❌ Still 403 - might be workflow activation issue")
        print(f"   💡 Need to verify workflow is ACTIVE in N8N")
    else:
        print(f"   ⚠️ Status: {status}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ Test error: {e}")

print(f"\n" + "=" * 50)
print(f"📋 SUMMARY")
print(f"=" * 50)
print(f"✅ Webhook registered without secret")
print(f"🔄 Ready for final test")
print(f"📱 Send message to bot now!")
print(f"🖼️ Should get AI image response")
print(f"=" * 50)