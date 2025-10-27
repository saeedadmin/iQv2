#!/usr/bin/env python3
"""
Set webhook with simple secret and test end-to-end
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"
SIMPLE_SECRET = "n8n_webhook_secret_123"  # Simple secret

print("🔐 SETTING WEBHOOK WITH SECRET")
print("=" * 50)
print(f"🔑 Using secret: {SIMPLE_SECRET}")
print(f"🔗 URL: {WEBHOOK_URL}")

# Step 1: Delete webhook
print(f"\n🗑️ Step 1: Deleting existing webhook...")
delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
delete_data = {"drop_pending_updates": True}

try:
    response = requests.post(delete_url, json=delete_data, timeout=10)
    result = response.json()
    print(f"✅ Webhook deleted")
except Exception as e:
    print(f"❌ Delete error: {e}")

# Step 2: Wait
time.sleep(3)

# Step 3: Register with simple secret
print(f"\n📝 Step 2: Registering webhook WITH SECRET...")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": WEBHOOK_URL,
    "max_connections": 40,
    "allowed_updates": ["message"],
    "secret_token": SIMPLE_SECRET
}

try:
    response = requests.post(register_url, json=register_data, timeout=10)
    result = response.json()
    print(f"📝 Register result: {json.dumps(result, indent=2)}")
    
    if result.get("ok") and result.get("result"):
        print(f"✅ SUCCESS! Webhook registered with secret!")
    else:
        print(f"❌ Registration failed: {result}")
        
except Exception as e:
    print(f"❌ Registration error: {e}")

# Step 4: Verify
print(f"\n✅ Step 3: Verifying webhook...")
time.sleep(3)

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
            print(f"   ✅ No errors!")
    
except Exception as e:
    print(f"❌ Verification error: {e}")

# Step 5: Test with secret header
print(f"\n🧪 Step 4: Testing webhook WITH SECRET...")
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Test with secret"
    }
}

headers = {
    "X-Telegram-Bot-Api-Secret-Token": SIMPLE_SECRET
}

try:
    response = requests.post(WEBHOOK_URL, json=test_data, headers=headers, timeout=15)
    status = response.status_code
    
    print(f"   📊 Response Code: {status}")
    
    if status == 200:
        print(f"   🎉 SUCCESS! Webhook working with secret!")
        print(f"   ✅ Workflow processing message!")
        print(f"   🚀 Bot should work end-to-end!")
    elif status == 403:
        print(f"   ❌ Still 403 - secret issue persists")
        print(f"   💡 N8N might need secret configuration")
    else:
        print(f"   ⚠️ Status: {status}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ Test error: {e}")

# Step 6: Test without secret (for comparison)
print(f"\n🔍 Step 5: Testing WITHOUT secret (comparison)...")
try:
    response = requests.post(WEBHOOK_URL, json=test_data, timeout=15)
    status = response.status_code
    
    print(f"   📊 Response Code (no secret): {status}")
    
    if status == 403 and "secret" in response.text.lower():
        print(f"   ✅ Confirmed: Secret validation required")
    else:
        print(f"   ⚠️ Unexpected response")
        
except Exception as e:
    print(f"   ❌ Comparison test error: {e}")

print(f"\n" + "=" * 50)
print(f"📋 NEXT STEPS")
print(f"=" * 50)
print(f"1. 🔑 Secret set: {SIMPLE_SECRET}")
print(f"2. 📱 Test bot with secret header")
print(f"3. 🖼️ Should get AI image")
print(f"4. 🔧 If still fails, check N8N secret settings")
print(f"=" * 50)

print(f"\n💡 N8N CONFIGURATION NEEDED:")
print(f"In N8N Telegram trigger node, set:")
print(f"- Webhook URL: {WEBHOOK_URL}")
print(f"- Secret Token: {SIMPLE_SECRET}")
print(f"- Or disable secret validation in node settings")