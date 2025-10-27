#!/usr/bin/env python3
"""
Emergency fix for webhook registration - Force domain registration and drop pending updates
"""

import requests
import json

BOT_TOKEN = "1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc"
WORKFLOW_ID = "ff17baeb-3182-41c4-b60a-e6159b02023b"
WEBHOOK_URL = f"https://iqv2.onrender.com/webhook/{WORKFLOW_ID}/webhook"

print("🚨 EMERGENCY WEBHOOK FIX")
print("=" * 50)
print(f"📍 Target URL: {WEBHOOK_URL}")

# Step 1: Delete webhook and drop ALL pending updates
print("\n🗑️ Step 1: Deleting webhook and dropping pending updates...")
delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
delete_data = {"drop_pending_updates": True}

try:
    response = requests.post(delete_url, json=delete_data, timeout=10)
    delete_result = response.json()
    print(f"Delete result: {json.dumps(delete_result, indent=2, ensure_ascii=False)}")
    
    if delete_result.get("ok") and delete_result.get("result"):
        print("✅ Webhook deleted and pending updates dropped")
    else:
        print("❌ Failed to delete webhook")
        
except Exception as e:
    print(f"❌ Error deleting webhook: {e}")

# Step 2: Wait a moment for Telegram to process deletion
print("\n⏳ Waiting 3 seconds for Telegram to process...")
import time
time.sleep(3)

# Step 3: Register webhook with DOMAIN (not IP)
print(f"\n📝 Step 2: Registering webhook with DOMAIN...")
register_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
register_data = {
    "url": WEBHOOK_URL,
    "max_connections": 40,
    "allowed_updates": ["message"]
}

try:
    response = requests.post(register_url, json=register_data, timeout=10)
    register_result = response.json()
    print(f"Register result: {json.dumps(register_result, indent=2, ensure_ascii=False)}")
    
    if register_result.get("ok") and register_result.get("result"):
        print("✅ Webhook successfully registered with domain!")
    else:
        print("❌ Failed to register webhook")
        
except Exception as e:
    print(f"❌ Error registering webhook: {e}")

# Step 4: Verify registration
print(f"\n✅ Step 3: Verifying registration...")
time.sleep(2)

info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
try:
    response = requests.get(info_url, timeout=10)
    info_result = response.json()
    
    if info_result.get("ok"):
        webhook_info = info_result["result"]
        url = webhook_info["url"]
        ip_address = webhook_info["ip_address"]
        pending = webhook_info["pending_update_count"]
        
        print(f"\n📊 REGISTRATION STATUS:")
        print(f"   URL: {url}")
        print(f"   IP: {ip_address}")
        print(f"   Pending: {pending}")
        
        if 'last_error_message' in webhook_info:
            print(f"   Last Error: {webhook_info['last_error_message']}")
        else:
            print(f"   Status: No errors!")
            
        # Check if using domain vs IP
        if "iqv2.onrender.com" in url:
            print(f"\n🎉 SUCCESS! Using DOMAIN (not IP)")
        else:
            print(f"\n⚠️ Still using IP address instead of domain")
            
        if pending == 0:
            print(f"✅ No pending updates - all clear!")
        else:
            print(f"⚠️ Still has {pending} pending updates")
    
except Exception as e:
    print(f"❌ Error checking webhook info: {e}")

print("\n" + "=" * 50)
print("🔄 NEXT STEPS:")
print("=" * 50)
print("1. ✅ Webhook registration completed")
print("2. 🔄 Try sending a message to your bot again")
print("3. 📱 Bot should respond now")
print("4. 🖼️ Check if AI image generation works")
print("=" * 50)