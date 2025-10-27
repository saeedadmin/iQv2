#!/usr/bin/env python3
"""
Quick 5-second test: Run AFTER activating workflow
"""

import requests

WEBHOOK_URL = "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook"

print("🚀 QUICK WORKFLOW TEST")
print("=" * 30)

test_data = {"test": "quick"}
try:
    response = requests.post(WEBHOOK_URL, json=test_data, timeout=10)
    status = response.status_code
    
    if status == 200:
        print(f"🎉 SUCCESS! Workflow ACTIVE!")
        print(f"✅ Bot should work now!")
        print(f"📱 Send: 'generate a beautiful landscape'")
    elif status == 403:
        print(f"❌ FAILED! Workflow still INACTIVE")
        print(f"🔧 Go to N8N and activate workflow")
    else:
        print(f"⚠️ Status: {status}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=" * 30)