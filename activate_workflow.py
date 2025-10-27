#!/usr/bin/env python3
"""
Script to activate N8N workflow via web interface
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

def setup_driver():
    """Setup Chrome driver for headless browser"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login_to_n8n(driver):
    """Login to N8N interface"""
    driver.get("https://iqv2.onrender.com")
    time.sleep(3)
    
    try:
        # Wait for login form
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        # Fill in credentials from environment variables
        # Note: These would need to be set as environment variables
        username = os.getenv('N8N_BASIC_AUTH_USER', 'admin')
        password = os.getenv('N8N_BASIC_AUTH_PASSWORD', 'password123')
        
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        
        # Submit login form
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for login to complete
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'workflows-list')]"))
        )
        
        print("✅ Successfully logged into N8N")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def activate_workflow(driver, workflow_id):
    """Activate the specific workflow"""
    try:
        # Navigate to the specific workflow
        workflow_url = f"https://iqv2.onrender.com/workflows/{workflow_id}"
        driver.get(workflow_url)
        
        # Wait for workflow to load
        time.sleep(3)
        
        # Look for the activate toggle button
        # This might be in different locations, try multiple selectors
        toggle_selectors = [
            "//button[contains(@class, 'workflow-active-toggle')]",
            "//span[contains(text(), 'Active') or contains(text(), 'Inactive')]",
            "//div[contains(@class, 'active-switch')]",
            "//button[contains(@class, 'toggle')]"
        ]
        
        for selector in toggle_selectors:
            try:
                toggle_element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                toggle_element.click()
                print(f"✅ Successfully clicked toggle using selector: {selector}")
                time.sleep(2)
                return True
            except:
                continue
        
        print("❌ Could not find workflow toggle button")
        return False
        
    except Exception as e:
        print(f"❌ Failed to activate workflow: {e}")
        return False

def main():
    """Main function"""
    workflow_id = "5b347b5d-8f35-45b3-a499-de95153088f0"
    
    print("🚀 Starting N8N workflow activation...")
    
    driver = setup_driver()
    
    try:
        if login_to_n8n(driver):
            if activate_workflow(driver, workflow_id):
                print(f"✅ Workflow {workflow_id} activated successfully!")
                
                # Test the webhook
                test_webhook(workflow_id)
            else:
                print("❌ Failed to activate workflow")
        else:
            print("❌ Failed to login to N8N")
            
    finally:
        driver.quit()

def test_webhook(workflow_id):
    """Test the webhook after activation"""
    webhook_url = f"https://iqv2.onrender.com/webhook/{workflow_id}/webhook"
    
    test_data = {
        "message": {
            "message_id": 123,
            "from": {"id": 327459477, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 327459477, "type": "private"},
            "date": 1699999999,
            "text": "hello"
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"🔗 Webhook test result:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ Webhook is working correctly!")
        else:
            print("⚠️ Webhook responded but may need attention")
            
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")

if __name__ == "__main__":
    main()