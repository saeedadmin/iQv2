#!/usr/bin/env python3
"""
Quick test for workflow activation - Run this immediately after activating workflow
"""

import requests
import json
import time

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WEBHOOK_URL = "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook"

print("🚀 QUICK WORKFLOW TEST")
print("=" * 30)
print("Run this AFTER activating workflow!")
print("=" * 30)

# Test with Telegram-style data
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
        "chat": {"id": 327459477, "type": "private"},
        "date": int(time.time()),
        "text": "Quick test"
    }
}

print(f"\n📤 Testing webhook...")
print(f"🔗 URL: {WEBHOOK_URL}")

try:
    response = requests.post(WEBHOOK_URL, json=test_data, timeout=10)
    status = response.status_code
    
    print(f"\n📊 Response Code: {status}")
    
    if status == 200:
        print(f"🎉 SUCCESS! Workflow is ACTIVE!")
        print(f"✅ Bot should work now!")
        print(f"📱 Try sending a message to your bot")
        
    elif status == 403:
        print(f"❌ FAILED! Workflow is still INACTIVE")
        print(f"🔧 Go back to N8N and make sure:")
        print(f"   1. Toggle is ON/Active")
        print(f"   2. Workflow is saved")
        print(f"   3. Page is refreshed")
        
    else:
        print(f"⚠️ Unexpected response: {status}")
        print(f"Response: {response.text[:100]}")
        
except requests.exceptions.Timeout:
    print(f"⏰ Timeout - Server not responding")
except Exception as e:
    print(f"❌ Error: {e}")

print(f"\n📱 Ready to test? Send message to bot:")
print(f"'generate a beautiful landscape'")
print("=" * 30)