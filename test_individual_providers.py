#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
تست جداگانه هر provider
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from handlers.ai.multi_provider_handler import MultiProviderHandler

async def test_specific_provider(provider_name: str):
    """تست یک provider خاص"""
    print(f"\n🧪 تست {provider_name.upper()}...")
    
    handler = MultiProviderHandler()
    
    try:
        # اگر provider مشخصی خواستیم، می‌توانیم اولویت آن را تنظیم کنیم
        if provider_name in handler.providers:
            # اولویت provider مورد نظر را به بالاترین می‌بریم
            for name in handler.providers:
                handler.providers[name]['priority'] = 5  # همه را پایین می‌بریم
            handler.providers[provider_name]['priority'] = 1  # مورد نظر را بالا می‌بریم
        
        test_message = f"سلام! تو کدام provider هستی و چه مدلی؟"
        result = await handler.send_message(test_message)
        
        if result['success']:
            print(f"✅ {provider_name} موفق:")
            print(f"   🤖 پاسخ: {result['content'][:150]}...")
            print(f"   🧠 مدل: {result['model']}")
            print(f"   🔑 کلید: {result.get('api_key_used', 'N/A')}")
            return True
        else:
            print(f"❌ {provider_name} ناموفق: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"💥 خطا در {provider_name}: {e}")
        return False

async def main():
    """تست جداگانه providers"""
    print("🎯 تست جداگانه هر Provider")
    print("=" * 50)
    
    providers_to_test = ['groq', 'cerebras', 'gemini', 'openrouter', 'cohere']
    
    results = {}
    for provider in providers_to_test:
        success = await test_specific_provider(provider)
        results[provider] = success
        await asyncio.sleep(1)  # صبر کوتاه بین تست‌ها
    
    print("\n🏆 خلاصه نتایج:")
    print("=" * 50)
    
    for provider, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {provider.upper()}")
    
    successful_providers = sum(results.values())
    print(f"\n📊 موفق: {successful_providers}/{len(providers_to_test)}")

if __name__ == "__main__":
    asyncio.run(main())