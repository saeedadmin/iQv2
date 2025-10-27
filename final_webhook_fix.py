#!/usr/bin/env python3
"""
FINAL webhook fix - Force domain registration and test end-to-end
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
DOMAIN_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

print("🔧 FINAL WEBHOOK FIX")
print("=" * 50)
print(f"🎯 Target: {DOMAIN_URL}")

# Step 1: Delete webhook completely
print(f"\n🗑️ Step 1: Completely deleting webhook...")
delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
delete_data = {"drop_pending_updates": True}

try:
    response = requests.post(delete_url, json=delete_data, timeout=10)
    result = response.json()
    print(f"Delete result: {json.dumps(result, indent=2)}")
    
    if result.get("ok") and result.get("result"):
        print(f"✅ Webhook completely deleted")
    else:
        print(f"❌ Delete failed: {result}")
        
except Exception as e:
    print(f"❌ Delete error: {e}")

# Step 2: Wait for Telegram to process
print(f"\n⏳ Waiting 5 seconds for Telegram to process...")
time.sleep(5)

# Step 3: Register with DOMAIN (not IP)
print(f"\n📝 Step 2: Registering webhook with DOMAIN...")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": DOMAIN_URL,
    "max_connections": 40,
    "allowed_updates": ["message"]
}

try:
    response = requests.post(register_url, json=register_data, timeout=10)
    result = response.json()
    print(f"Register result: {json.dumps(result, indent=2)}")
    
    if result.get("ok") and result.get("result"):
        print(f"✅ SUCCESS! Webhook registered with DOMAIN!")
    else:
        print(f"❌ Registration failed: {result}")
        
except Exception as e:
    print(f"❌ Registration error: {e}")

# Step 4: Verify and check status
print(f"\n✅ Step 3: Verifying webhook registration...")
time.sleep(3)

info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(info_url, timeout=10)
    result = response.json()
    
    if result.get("ok"):
        info = result["result"]
        print(f"\n📊 WEBHOOK STATUS:")
        print(f"   🔗 URL: {info['url']}")
        print(f"   🌐 IP: {info['ip_address']}")
        print(f"   ⏳ Pending: {info['pending_update_count']}")
        
        if info.get("last_error_message"):
            print(f"   ❌ Error: {info['last_error_message']}")
        else:
            print(f"   ✅ No errors!")
            
        # Critical checks
        if "iqv2.onrender.com" in info['url']:
            print(f"\n🎉 PERFECT! Using DOMAIN (not IP)")
        else:
            print(f"\n⚠️ WARNING! Still using IP instead of domain")
            
        if info['pending_update_count'] == 0:
            print(f"✅ No pending updates")
        else:
            print(f"⚠️ Still has {info['pending_update_count']} pending updates")
    
except Exception as e:
    print(f"❌ Verification error: {e}")

# Step 5: Test actual workflow
print(f"\n🧪 Step 4: Testing actual workflow...")
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Final test message"
    }
}

try:
    response = requests.post(DOMAIN_URL, json=test_data, timeout=15)
    status = response.status_code
    
    print(f"   📊 Workflow Response: {status}")
    
    if status == 200:
        print(f"   🎉 SUCCESS! Workflow is ACTIVE and processing!")
        print(f"   ✅ Bot should work end-to-end!")
    elif status == 403:
        print(f"   ❌ FAILED! Workflow might not be active")
    else:
        print(f"   ⚠️ Unexpected status: {status}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print(f"   ⏰ Timeout - Workflow taking too long")
except Exception as e:
    print(f"   ❌ Test error: {e}")

print(f"\n" + "=" * 50)
print(f"🚀 FINAL STATUS")
print(f"=" * 50)
print(f"📱 Ready to test your bot!")
print(f"🔄 Send message: 'generate a beautiful landscape'")
print(f"🖼️ Should get AI image response")
print(f"=" * 50)