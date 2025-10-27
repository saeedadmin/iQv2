#!/usr/bin/env python3
"""
Fix workflow activation issue - Check and activate workflow
"""

import requests
import json

# N8N Configuration
N8N_BASE_URL = "https://iqv2.onrender.com"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"

print("🔧 WORKFLOW ACTIVATION FIX")
print("=" * 50)

# Step 1: Check current webhook status
print("\n1. 📡 Current Webhook Status:")
webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(webhook_url)
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

# Step 2: Test webhook endpoint with correct authentication
print(f"\n2. 🧪 Testing Webhook Endpoint:")
test_url = f"{N8N_BASE_URL}/webhook/{WORKFLOW_ID}/webhook"

# Try different approaches to test webhook
test_data = {
    "update_id": 123456789,
    "message": {
        "message_id": 999,
        "from": {"id": 327459477, "is_bot": False},
        "chat": {"id": 327459477, "type": "private"},
        "text": "test message"
    }
}

print(f"   📤 Testing endpoint: {test_url}")

# Method 1: Try with proper headers
headers = {
    "Content-Type": "application/json",
    "User-Agent": "TelegramBot",
    "X-Telegram-Bot-Api-Secret-Token": ""  # Empty token test
}

try:
    response = requests.post(test_url, json=test_data, headers=headers, timeout=10)
    status = response.status_code
    print(f"   📊 Response Code: {status}")
    
    if status == 200:
        print(f"   ✅ Webhook working! (This means workflow might be active)")
    elif status == 403:
        print(f"   ❌ 403 Forbidden - Workflow likely not active")
        print(f"   💡 Need to activate workflow in N8N interface")
    elif status == 404:
        print(f"   ❌ 404 Not Found - Wrong workflow ID")
    else:
        print(f"   ⚠️ Unexpected response: {status}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print(f"   ⏰ Timeout - Server not responding properly")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Try to trigger workflow activation via API (if possible)
print(f"\n3. 🔄 Attempting Workflow Activation:")
print(f"   📍 Manual steps needed:")

# This is a guide since we can't directly activate via API
print(f"   Step 1: Visit N8N interface")
print(f"   Step 2: Go to workflow: {N8N_BASE_URL}/workflows/{WORKFLOW_ID}")
print(f"   Step 3: Look for the ON/OFF toggle switch")
print(f"   Step 4: Make sure it's ON (active)")
print(f"   Step 5: Save and test")

# Step 4: Clear pending updates and re-register
print(f"\n4. 🔄 Clearing Pending Updates:")
clear_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
clear_data = {"drop_pending_updates": True}

try:
    response = requests.post(clear_url, json=clear_data, timeout=10)
    result = response.json()
    
    if result.get("ok") and result.get("result"):
        print(f"   ✅ Pending updates cleared")
    else:
        print(f"   ❌ Failed to clear: {result}")
        
except Exception as e:
    print(f"   ❌ Error clearing: {e}")

# Step 5: Re-register webhook
print(f"\n5. 📝 Re-registering Webhook:")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": f"{N8N_BASE_URL}/webhook/{WORKFLOW_ID}/webhook",
    "max_connections": 40,
    "allowed_updates": ["message"]
}

try:
    response = requests.post(register_url, json=register_data, timeout=10)
    result = response.json()
    
    if result.get("ok") and result.get("result"):
        print(f"   ✅ Webhook re-registered")
    else:
        print(f"   ❌ Re-registration failed: {result}")
        
except Exception as e:
    print(f"   ❌ Error re-registering: {e}")

print("\n" + "=" * 50)
print("🚀 NEXT STEPS")
print("=" * 50)
print("1. 🔧 MUST: Activate workflow manually in N8N interface")
print("2. 📱 Test: Send message to bot")
print("3. 🔍 Check: N8N workflow executions")
print("4. 📊 Monitor: Pending updates should become 0")
print("=" * 50)

print("\n⚡ QUICK ACTIONS:")
print(f"- Open: {N8N_BASE_URL}/workflows/{WORKFLOW_ID}")
print(f"- Look for: Toggle switch (ON/OFF)")
print(f"- Ensure: Workflow is ACTIVE (ON)")
print(f"- Then: Send test message to bot")