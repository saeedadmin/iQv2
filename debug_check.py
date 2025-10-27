#!/usr/bin/env python3
"""
Debug script to check webhook and workflow status
"""

import requests
import json

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"

print("🔍 DEBUG: Checking Webhook and System Status")
print("=" * 50)

# 1. Check webhook registration
print("\n1. 📡 Webhook Registration Status:")
webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(webhook_url)
    result = response.json()
    
    if result.get("ok"):
        info = result["result"]
        print(f"   ✅ Webhook URL: {info['url']}")
        print(f"   ✅ IP Address: {info['ip_address']}")
        print(f"   ✅ Pending Updates: {info['pending_update_count']}")
        
        if info.get("last_error_message"):
            print(f"   ❌ Last Error: {info['last_error_message']}")
        else:
            print(f"   ✅ No errors")
            
        # Check if using domain
        if "iqv2.onrender.com" in info['url']:
            print(f"   ✅ Using DOMAIN (good!)")
        else:
            print(f"   ❌ Using IP instead of domain")
            
except Exception as e:
    print(f"   ❌ Error checking webhook: {e}")

# 2. Check webhook endpoint accessibility
print("\n2. 🌐 Webhook Endpoint Test:")
test_url = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"
try:
    response = requests.post(test_url, json={"test": "debug"}, timeout=5)
    if response.status_code == 403:
        print(f"   ✅ Endpoint accessible (HTTP 403 = normal)")
    else:
        print(f"   ⚠️ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   ❌ Endpoint not accessible: {e}")

# 3. Check N8N interface
print("\n3. 🖥️ N8N Interface Test:")
n8n_url = "https://iqv2.onrender.com"
try:
    response = requests.get(n8n_url, timeout=5)
    if response.status_code == 200:
        print(f"   ✅ N8N interface accessible")
    else:
        print(f"   ❌ N8N interface issue: {response.status_code}")
except Exception as e:
    print(f"   ❌ N8N interface not accessible: {e}")

# 4. Manual test message
print("\n4. 📤 Sending Manual Test Message:")
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
test_data = {
    "chat_id": "327459477",
    "text": "🔧 Debug test from MiniMax Agent - if you see this, webhook is working!"
}

try:
    response = requests.post(send_url, json=test_data, timeout=5)
    result = response.json()
    
    if result.get("ok"):
        print(f"   ✅ Test message sent successfully")
        print(f"   📱 Message ID: {result['result']['message_id']}")
    else:
        print(f"   ❌ Failed to send message: {result}")
        
except Exception as e:
    print(f"   ❌ Error sending message: {e}")

print("\n" + "=" * 50)
print("📋 DEBUG SUMMARY")
print("=" * 50)
print("If all checks above are ✅, then:")
print("1. 🔄 Try sending a message to your bot")
print("2. 📱 Check if bot responds")
print("3. 🖼️ Verify AI image generation")
print("4. 🔍 Check N8N workflow execution history")
print("=" * 50)

print("\n🔧 TROUBLESHOOTING:")
print("- If webhook shows pending updates > 0: webhook registration failed")
print("- If N8N interface not accessible: server might be restarting")
print("- If bot doesn't respond: check workflow is ACTIVE in N8N")
print("- If AI generation fails: check API keys in N8N credentials")