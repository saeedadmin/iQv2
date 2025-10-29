#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت debug برای مشکل ترجمه
نویسنده: MiniMax Agent
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# لود متغیرهای محیطی
load_dotenv()

# اضافه کردن مسیر modules
sys.path.append('/workspace')

from handlers.ai.ai_chat_handler import GeminiChatHandler
from handlers.ai.multi_provider_handler import MultiProviderHandler

async def test_multi_provider():
    """تست MultiProvider Handler"""
    print("🔍 شروع تست MultiProvider Handler...")
    
    try:
        # تست مستقیم MultiProvider
        print("\n📋 تست مستقیم MultiProviderHandler:")
        multi_handler = MultiProviderHandler()
        
        if multi_handler:
            print("✅ MultiProviderHandler ایجاد شد")
            
            # بررسی وضعیت providers
            status = multi_handler.get_status()
            print(f"📊 وضعیت providers: {status}")
            
            # تست ترجمه
            test_texts = [
                "OpenAI announces new AI model",
                "Bitcoin reaches new price record",
                "Technology company launches innovative product"
            ]
            
            print(f"\n🌐 تست ترجمه {len(test_texts)} متن:")
            print("متن‌های اصلی:", test_texts)
            
            translated = await multi_handler.translate_multiple_texts(test_texts)
            
            print("نتایج ترجمه:")
            for i, (original, translated_text) in enumerate(zip(test_texts, translated), 1):
                print(f"{i}. Original: {original}")
                print(f"   Translated: {translated_text}")
                print("---")
        else:
            print("❌ MultiProviderHandler ایجاد نشد")
            
    except Exception as e:
        print(f"❌ خطا در MultiProviderHandler: {e}")
        import traceback
        traceback.print_exc()

async def test_gemini_chat_handler():
    """تست GeminiChatHandler با MultiProvider"""
    print("\n🤖 تست GeminiChatHandler:")
    
    try:
        handler = GeminiChatHandler()
        
        # بررسی وضعیت
        status = handler.get_quota_status()
        print(f"📊 وضعیت handler: {status}")
        
        # تست ترجمه
        test_texts = [
            "OpenAI announces new AI model",
            "Bitcoin reaches new price record", 
            "Technology company launches innovative product"
        ]
        
        print(f"\n🌐 تست ترجمه {len(test_texts)} متن با GeminiChatHandler:")
        
        translated = await handler.translate_multiple_texts(test_texts)
        
        print("نتایج ترجمه:")
        for i, (original, translated_text) in enumerate(zip(test_texts, translated), 1):
            print(f"{i}. Original: {original}")
            print(f"   Translated: {translated_text}")
            print("---")
            
    except Exception as e:
        print(f"❌ خطا در GeminiChatHandler: {e}")
        import traceback
        traceback.print_exc()

async def test_public_menu_gemini():
    """تست GeminiChatHandler همانند public_menu"""
    print("\n📰 تست GeminiChatHandler مثل public_menu:")
    
    try:
        # همانند public_menu.py
        handler = GeminiChatHandler()
        
        # بررسی using_multi
        print(f"🔍 using_multi: {handler.using_multi}")
        print(f"🔍 multi_handler: {handler.multi_handler}")
        
        # تست ترجمه
        test_texts = [
            "OpenAI announces new AI model",
            "Bitcoin reaches new price record",
            "Technology company launches innovative product"
        ]
        
        print(f"\n🌐 تست ترجمه {len(test_texts)} متن:")
        
        translated = await handler.translate_multiple_texts(test_texts)
        
        print("نتایج ترجمه:")
        for i, (original, translated_text) in enumerate(zip(test_texts, translated), 1):
            print(f"{i}. Original: {original}")
            print(f"   Translated: {translated_text}")
            print("---")
            
    except Exception as e:
        print(f"❌ خطا در public_menu-like test: {e}")
        import traceback
        traceback.print_exc()

async def check_environment():
    """بررسی متغیرهای محیطی"""
    print("🔍 بررسی متغیرهای محیطی:")
    
    # بررسی کلیدهای موجود
    keys_to_check = [
        'GEMINI_API_KEY',
        'GEMINI_API_KEY_2', 
        'GROQ_API_KEY',
        'GROQ_API_KEY_2',
        'CEREBRAS_API_KEY',
        'CEREBRAS_API_KEY_2'
    ]
    
    for key in keys_to_check:
        value = os.getenv(key)
        if value:
            print(f"✅ {key}: {value[:10]}...")
        else:
            print(f"❌ {key}: NOT SET")

async def main():
    """تست اصلی"""
    print("🚀 شروع debug ترجمه...")
    
    await check_environment()
    await test_multi_provider()
    await test_gemini_chat_handler()
    await test_public_menu_gemini()
    
    print("\n🏁 تست تمام شد!")

if __name__ == "__main__":
    asyncio.run(main())