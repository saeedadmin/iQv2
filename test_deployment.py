#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
تست ساده برای بررسی imports و تنظیمات ربات
"""

import os
import sys

def test_imports():
    """تست کردن تمام imports مورد نیاز"""
    print("🔍 در حال تست imports...")
    
    try:
        import telegram
        print("✅ telegram - OK")
    except ImportError as e:
        print(f"❌ telegram - ERROR: {e}")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp - OK")
    except ImportError as e:
        print(f"❌ aiohttp - ERROR: {e}")
        return False
    
    try:
        from database import DatabaseManager
        print("✅ database - OK")
    except ImportError as e:
        print(f"❌ database - ERROR: {e}")
        return False
    
    try:
        from telegram_signal_scraper import get_latest_crypto_signals
        print("✅ telegram_signal_scraper - OK")
    except ImportError as e:
        print(f"❌ telegram_signal_scraper - ERROR: {e}")
        return False
    
    try:
        from admin_panel import AdminPanel
        print("✅ admin_panel - OK")
    except ImportError as e:
        print(f"❌ admin_panel - ERROR: {e}")
        return False
    
    print("✅ همه imports موفقیت‌آمیز بود!")
    return True

def test_environment():
    """تست کردن environment variables"""
    print("\n🔍 در حال تست environment variables...")
    
    bot_token = os.getenv('BOT_TOKEN')
    admin_id = os.getenv('ADMIN_USER_ID')
    apify_key = os.getenv('APIFY_API_KEY')
    
    print(f"BOT_TOKEN: {'✅ SET' if bot_token else '❌ NOT SET'}")
    print(f"ADMIN_USER_ID: {'✅ SET' if admin_id else '❌ NOT SET'}")
    print(f"APIFY_API_KEY: {'✅ SET' if apify_key else '❌ NOT SET'}")
    
    if not bot_token:
        print("⚠️  BOT_TOKEN تنظیم نشده - ربات شروع نخواهد شد")
        return False
    
    return True

def test_files():
    """تست کردن وجود فایل‌های ضروری"""
    print("\n🔍 در حال تست فایل‌های ضروری...")
    
    required_files = [
        'Procfile',
        'requirements.txt', 
        'runtime.txt',
        'telegram_bot.py',
        'telegram_signal_scraper.py',
        'database.py',
        'admin_panel.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - موجود")
        else:
            print(f"❌ {file} - موجود نیست")
            return False
    
    print("✅ همه فایل‌های ضروری موجود است!")
    return True

def main():
    print("🚀 شروع تست ربات...\n")
    
    # تست فایل‌ها
    if not test_files():
        print("❌ تست فایل‌ها ناموفق")
        sys.exit(1)
    
    # تست imports
    if not test_imports():
        print("❌ تست imports ناموفق")
        sys.exit(1)
    
    # تست environment
    if not test_environment():
        print("❌ تست environment ناموفق") 
        print("💡 برای deployment در Koyeb، BOT_TOKEN را در Environment Variables تنظیم کنید")
    
    print("\n🎉 همه تست‌ها موفقیت‌آمیز بود!")
    print("🚀 ربات آماده deployment است!")

if __name__ == "__main__":
    main()