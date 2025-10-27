#!/usr/bin/env python3
"""
Script to configure N8N webhook URL directly
"""

import requests
import json
import time

def configure_webhook():
    """Configure webhook URL for Telegram trigger"""
    
    # N8N API endpoint
    base_url = "https://iqv2.onrender.com"
    workflow_id = "ff17baeb-3182-41c4-b60a-e6159b02023b"
    
    # Public webhook URL (correct one)
    correct_webhook_url = f"https://iqv2.onrender.com/webhook/{workflow_id}/webhook"
    
    print(f"🎯 Target: Configure webhook for workflow {workflow_id}")
    print(f"🔗 Correct webhook URL: {correct_webhook_url}")
    print(f"❌ Wrong webhook URL: https://localhost:8443/webhook/{workflow_id}/webhook")
    print("")
    
    # API endpoints to try
    endpoints = [
        f"/api/v1/workflows/{workflow_id}",
        f"/api/v1/workflows/{workflow_id}/node-telegrambot",
        "/api/v1/workflows",
        "/api/v1/active-workflows"
    ]
    
    for endpoint in endpoints:
        print(f"🔍 Trying endpoint: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", 
                                  headers={"Accept": "application/json"},
                                  timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 401]:
                print(f"   Response preview: {response.text[:200]}...")
                break
            else:
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n💡 Manual Steps Required:")
    print("1. Go to N8N interface: https://iqv2.onrender.com")
    print("2. Open workflow with ID: ff17baeb-3182-41c4-b60a-e6159b02023b")
    print("3. Click on Telegram Bot trigger node")
    print("4. Look for 'Webhook URL' or 'Set Webhook' setting")
    print("5. Replace 'localhost:8443' with 'iqv2.onrender.com:8443'")
    print("6. Or delete and recreate the webhook with correct URL")
    
    print("\n🎛️  N8N Interface Navigation:")
    print("- Navigate to workflow: https://iqv2.onrender.com/workflows/ff17baeb-3182-41c4-b60a-e6159b02023b")
    print("- Click on Telegram node")
    print("- In node settings, find webhook configuration")
    print("- Update from: https://localhost:8443/webhook/...")
    print("- Update to: https://iqv2.onrender.com/webhook/...")

if __name__ == "__main__":
    configure_webhook()