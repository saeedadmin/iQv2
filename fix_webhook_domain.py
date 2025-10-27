#!/usr/bin/env python3
"""
Fix webhook registration to use proper domain and HTTPS
"""

import requests
import json

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

print("🔧 Fixing webhook registration...")
print(f"📍 New webhook URL: {WEBHOOK_URL}")

# 1. Delete existing webhook
print("\n🗑️ Deleting existing webhook...")
delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
delete_params = {"drop_pending_updates": True}
response = requests.post(delete_url, json=delete_params)
delete_result = response.json()
print(f"Delete result: {json.dumps(delete_result, indent=2)}")

# 2. Register new webhook with proper HTTPS
print(f"\n📝 Registering new webhook with domain...")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": WEBHOOK_URL,
    "max_connections": 40,
    "allowed_updates": ["message"]
}
response = requests.post(register_url, json=register_data)
register_result = response.json()
print(f"Register result: {json.dumps(register_result, indent=2)}")

# 3. Verify webhook info
print(f"\n✅ Verifying webhook registration...")
info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
info_response = requests.get(info_url)
info_result = info_response.json()
print(f"Webhook info: {json.dumps(info_result, indent=2, ensure_ascii=False)}")

# Check if registration was successful
if info_result.get("ok") and info_result["result"]["url"] == WEBHOOK_URL:
    print("\n🎉 SUCCESS! Webhook properly registered with domain!")
    print("✅ Telegram will now send messages to: " + WEBHOOK_URL)
else:
    print("\n❌ ERROR: Webhook registration failed!")

print(f"\n📊 Current status:")
if info_result.get("ok"):
    webhook_info = info_result["result"]
    print(f"   URL: {webhook_info['url']}")
    print(f"   IP: {webhook_info['ip_address']}")
    print(f"   Pending updates: {webhook_info['pending_update_count']}")
    
    if 'last_error_message' in webhook_info:
        print(f"   Last error: {webhook_info['last_error_message']}")