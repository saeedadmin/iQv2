#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت تست MultiProviderHandler
نویسنده: MiniMax Agent

این اسکریپت عملکرد MultiProviderHandler را تست می‌کند
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from handlers.ai.multi_provider_handler import MultiProviderHandler
    from handlers.ai.ai_chat_handler import GeminiChatHandler
except ImportError as e:
    print(f"❌ خطا در import: {e}")
    print("📁 مطمئن شوید که در مسیر درست هستید")
    sys.exit(1)

async def test_multi_provider():
    """تست کردن MultiProviderHandler"""
    print("🚀 شروع تست MultiProviderHandler...")
    
    try:
        # ایجاد handler
        handler = MultiProviderHandler()
        
        # بررسی وضعیت
        status = handler.get_status()
        print("\n📊 وضعیت Providers:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # تست ارسال پیام
        print("\n💬 تست ارسال پیام...")
        test_message = "سلام! این یک تست ساده است."
        
        result = await handler.send_message(test_message)
        
        print(f"✅ نتیجه: {result['success']}")
        if result['success']:
            print(f"🤖 پاسخ: {result['content'][:100]}...")
            print(f"🔧 Provider: {result['provider']}")
        else:
            print(f"❌ خطا: {result.get('error', 'Unknown error')}")
        
        # تست ترجمه گروهی
        print("\n🌐 تست ترجمه گروهی...")
        test_texts = [
            "Hello, this is a test message.",
            "AI is transforming the world.",
            "Multi-provider systems are powerful."
        ]
        
        translations = await handler.translate_multiple_texts(test_texts)
        
        print("✅ ترجمه‌ها:")
        for i, (original, translated) in enumerate(zip(test_texts, translations), 1):
            print(f"{i}. EN: {original}")
            print(f"   FA: {translated}")
            print()
        
        print("🎉 تست با موفقیت انجام شد!")
        
    except Exception as e:
        print(f"❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()

async def test_legacy_handler():
    """تست کردن GeminiChatHandler قدیمی"""
    print("\n🔄 تست GeminiChatHandler (Legacy)...")
    
    try:
        handler = GeminiChatHandler()
        
        # بررسی وضعیت
        status = handler.get_quota_status()
        print("📊 وضعیت Legacy Handler:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        print("✅ Legacy handler آماده است")
        
    except Exception as e:
        print(f"❌ خطا در Legacy handler: {e}")

def check_api_keys():
    """بررسی API keys موجود"""
    print("🔑 بررسی API Keys...")
    
    api_keys = {
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'CEREBRAS_API_KEY': os.getenv('CEREBRAS_API_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
        'COHERE_API_KEY': os.getenv('COHERE_API_KEY')
    }
    
    available_keys = 0
    for key_name, key_value in api_keys.items():
        if key_value and key_value.strip():
            print(f"✅ {key_name}: موجود")
            available_keys += 1
        else:
            print(f"❌ {key_name}: موجود نیست")
    
    print(f"\n📈 خلاصه: {available_keys}/5 API key موجود")
    
    if available_keys >= 2:
        print("🎯 حداقل 2 API key موجود - سیستم آماده است!")
    elif available_keys == 1:
        print("⚠️ فقط 1 API key موجود - عملکرد محدود")
    else:
        print("🚫 هیچ API key موجود نیست - سیستم کار نمی‌کند")
    
    return available_keys

def main():
    """تابع اصلی"""
    print("=" * 60)
    print("🧪 MULTI-PROVIDER AI HANDLER TEST SUITE")
    print("=" * 60)
    
    # بررسی API keys
    available_keys = check_api_keys()
    
    if available_keys == 0:
        print("\n❌ هیچ API key موجود نیست!")
        print("📝 برای استفاده از سیستم:")
        print("1. فایل .env.example را کپی کنید")
        print("2. API keys دریافت کنید")
        print("3. متغیرهای محیطی را تنظیم کنید")
        return
    
    # تست کردن سیستم
    if available_keys >= 1:
        asyncio.run(test_multi_provider())
    
    if available_keys >= 1:
        asyncio.run(test_legacy_handler())
    
    print("\n" + "=" * 60)
    print("✅ تست کامل شد!")
    print("=" * 60)

if __name__ == "__main__":
    main()