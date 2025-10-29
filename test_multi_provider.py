#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت تست Multi-Provider AI System (نسخه به‌روزرسانی شده)
نویسنده: MiniMax Agent

تست‌ها:
- Health check برای تمام providers
- تست ارسال پیام با providers مختلف
- تست ترجمه با providers مختلف
- نمایش آمار performance
- تست چرخش کلیدها
"""

import asyncio
import logging
import os
import sys
import json
from pathlib import Path

# اضافه کردن مسیر handlers
sys.path.append(str(Path(__file__).parent))

from handlers.ai.multi_provider_handler import MultiProviderHandler

# تنظیم logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiProviderTester:
    """تستر Multi-Provider System"""
    
    def __init__(self):
        self.handler = MultiProviderHandler()
        self.test_results = {}
    
    def check_api_keys(self):
        """بررسی API keys موجود"""
        print("🔑 بررسی API Keys...")
        
        api_keys = {
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
            'GROQ_API_KEY_2': os.getenv('GROQ_API_KEY_2'),
            'CEREBRAS_API_KEY': os.getenv('CEREBRAS_API_KEY'),
            'CEREBRAS_API_KEY_2': os.getenv('CEREBRAS_API_KEY_2'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'GEMINI_API_KEY_2': os.getenv('GEMINI_API_KEY_2'),
            'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
            'COHERE_API_KEY': os.getenv('COHERE_API_KEY')
        }
        
        available_keys = 0
        print("\nوضعیت کلیدها:")
        for key_name, key_value in api_keys.items():
            if key_value and key_value.strip():
                masked_key = key_value[:10] + "..." + key_value[-4:] if len(key_value) > 14 else key_value
                print(f"✅ {key_name}: {masked_key}")
                available_keys += 1
            else:
                print(f"❌ {key_name}: موجود نیست")
        
        print(f"\n📈 خلاصه: {available_keys}/{len(api_keys)} API key موجود")
        
        return available_keys
    
    async def test_health_check(self):
        """تست سلامت همه providers"""
        logger.info("🏥 شروع health check...")
        
        status = self.handler.get_status()
        print("\n=== وضعیت Providers ===")
        print(f"تعداد کل providers: {status['total_providers']}")
        print(f"providers فعال: {status['available_providers']}")
        print(f"providers خراب: {len(status['failed_providers'])}")
        
        # نمایش آمار هر provider
        for name, quota_info in status['quota_status'].items():
            priority_icons = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}
            priority_icon = priority_icons.get(quota_info['priority'], "❓")
            
            print(f"\n{priority_icon} {name.upper()}:")
            print(f"   ✅ فعال: {quota_info['available']}")
            print(f"   📊 درخواست‌های امروز: {quota_info['calls_today']}/{quota_info['max_daily']}")
            print(f"   🎯 اولویت: {quota_info['priority']}")
        
        # نمایش آمار کلیدها
        print("\n=== آمار کلیدها ===")
        for name, key_stats in status['key_rotator_stats'].items():
            print(f"\n🔑 {name.upper()}:")
            print(f"   📝 تعداد کلیدها: {key_stats['total_keys']}")
            print(f"   ❌ کلیدهای خراب: {key_stats['failed_keys']}")
            print(f"   📈 آمار استفاده:")
            for i, (key, usage) in enumerate(key_stats['usage_stats'].items(), 1):
                print(f"      کلید {i}: {usage} استفاده")
        
        # نمایش آمار performance
        print("\n=== آمار Performance ===")
        for name, perf in status['performance_stats'].items():
            if perf['total_requests'] > 0:
                speed_icon = "⚡" if perf['avg_response_time'] < 2 else "🐌"
                success_rate = perf['success_rate'] * 100
                print(f"\n{speed_icon} {name.upper()}:")
                print(f"   📊 نرخ موفقیت: {success_rate:.1f}%")
                print(f"   ⏱️ میانگین زمان پاسخ: {perf['avg_response_time']:.2f}s")
                print(f"   📈 تعداد کل درخواست‌ها: {perf['total_requests']}")
    
    async def test_single_provider(self, provider_name: str, test_message: str = "سلام! چطوری؟"):
        """تست یک provider مشخص"""
        logger.info(f"🎯 تست {provider_name}...")
        
        try:
            result = await self.handler.send_message(test_message)
            
            if result['success']:
                print(f"\n✅ {provider_name} موفق:")
                print(f"   🤖 پاسخ: {result['content'][:100]}...")
                print(f"   🔧 Provider: {result['provider']}")
                print(f"   🧠 مدل: {result['model']}")
                print(f"   🔑 کلید: {result.get('api_key_used', 'N/A')}")
                return True
            else:
                print(f"\n❌ {provider_name} ناموفق:")
                print(f"   🚫 خطا: {result['error']}")
                return False
                
        except Exception as e:
            print(f"\n💥 خطای غیرمنتظره در {provider_name}: {e}")
            return False
    
    async def test_all_providers(self):
        """تست تمام providers موجود"""
        logger.info("🚀 شروع تست تمام providers...")
        
        test_message = "سلام! لطفاً خودت را معرفی کن و بگو که چه مدلی هستی."
        
        providers_tested = 0
        providers_successful = 0
        
        # تست هر provider حداکثر 2 بار
        for attempt in range(2):
            for provider_name in self.handler.providers.keys():
                if provider_name not in self.test_results or not self.test_results[provider_name]:
                    success = await self.test_single_provider(provider_name, test_message)
                    self.test_results[provider_name] = success
                    
                    if success:
                        providers_successful += 1
                    
                    providers_tested += 1
                    
                    # صبر کوتاه بین تست‌ها
                    await asyncio.sleep(1)
        
        print(f"\n📊 خلاصه تست:")
        print(f"   ✅ موفق: {providers_successful}/{providers_tested}")
        print(f"   📈 نرخ موفقیت: {(providers_successful/providers_tested*100):.1f}%")
        
        return providers_successful > 0
    
    async def test_translation(self):
        """تست ترجمه"""
        logger.info("🌍 تست ترجمه...")
        
        test_texts = [
            "Hello, how are you?",
            "What is your name?", 
            "Thank you very much!"
        ]
        
        print("\n=== تست ترجمه ===")
        print("متن‌های ورودی:")
        for i, text in enumerate(test_texts, 1):
            print(f"   {i}. {text}")
        
        try:
            translated = await self.handler.translate_multiple_texts(test_texts)
            
            print("\nنتایج ترجمه:")
            for i, (original, translated_text) in enumerate(zip(test_texts, translated), 1):
                print(f"   {i}. {original} → {translated_text}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ خطا در تست ترجمه: {e}")
            return False
    
    async def test_load_balancing(self):
        """تست load balancing بین کلیدها"""
        logger.info("⚖️ تست load balancing...")
        
        print("\n=== تست Load Balancing ===")
        test_message = "پیام تست برای بررسی چرخش کلیدها"
        
        # ارسال چندین پیام
        for i in range(5):
            try:
                result = await self.handler.send_message(f"{test_message} ({i+1})")
                if result['success']:
                    print(f"   پیام {i+1}: ✅ کلید {result.get('api_key_used', 'N/A')}")
                else:
                    print(f"   پیام {i+1}: ❌ خطا")
                    
                await asyncio.sleep(0.5)  # صبر کوتاه
                
            except Exception as e:
                print(f"   پیام {i+1}: 💥 خطا - {e}")
        
        # نمایش آمار نهایی
        status = self.handler.get_status()
        print("\nآمار نهایی استفاده از کلیدها:")
        for name, key_stats in status['key_rotator_stats'].items():
            print(f"\n🔑 {name.upper()}:")
            for i, (key, usage) in enumerate(key_stats['usage_stats'].items(), 1):
                print(f"   کلید {i}: {usage} استفاده")
    
    async def test_performance_comparison(self):
        """تست مقایسه performance بین providers"""
        logger.info("🏃‍♂️ تست performance...")
        
        print("\n=== تست Performance Comparison ===")
        
        test_message = "لطفاً فقط بگو: 'پاسخ تست'"
        
        providers_performance = {}
        
        for provider_name in self.handler.providers.keys():
            try:
                times = []
                successes = 0
                attempts = 3
                
                for i in range(attempts):
                    start_time = asyncio.get_event_loop().time()
                    result = await self.handler.send_message(f"{test_message} {i+1}")
                    end_time = asyncio.get_event_loop().time()
                    
                    if result['success']:
                        times.append(end_time - start_time)
                        successes += 1
                    
                    await asyncio.sleep(0.5)
                
                if times:
                    avg_time = sum(times) / len(times)
                    providers_performance[provider_name] = {
                        'success_rate': successes / attempts,
                        'avg_response_time': avg_time,
                        'min_time': min(times),
                        'max_time': max(times)
                    }
                
            except Exception as e:
                print(f"   ❌ خطا در تست {provider_name}: {e}")
        
        # نمایش نتایج مرتب شده
        print("\n🏆 رتبه‌بندی Performance:")
        sorted_providers = sorted(
            providers_performance.items(),
            key=lambda x: (x[1]['success_rate'], -x[1]['avg_response_time']),
            reverse=True
        )
        
        for i, (name, perf) in enumerate(sorted_providers, 1):
            speed_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            success_rate = perf['success_rate'] * 100
            
            print(f"\n{speed_icon} {name.upper()}:")
            print(f"   📊 نرخ موفقیت: {success_rate:.0f}%")
            print(f"   ⏱️ میانگین زمان: {perf['avg_response_time']:.2f}s")
            print(f"   📈 سریع‌ترین: {perf['min_time']:.2f}s")
            print(f"   📉 کندترین: {perf['max_time']:.2f}s")
    
    async def run_all_tests(self):
        """اجرای تمام تست‌ها"""
        print("🧪 شروع تست کامل Multi-Provider AI System")
        print("=" * 60)
        
        # 0. بررسی API keys
        available_keys = self.check_api_keys()
        if available_keys == 0:
            print("\n❌ هیچ API key موجود نیست!")
            return
        
        print("\n" + "=" * 60)
        
        # 1. Health Check
        await self.test_health_check()
        print("\n" + "=" * 60)
        
        # 2. تست providers
        if available_keys >= 1:
            success = await self.test_all_providers()
            if not success:
                print("\n⚠️ هیچ provider موفق نبود!")
                return
        else:
            print("\n⚠️ هیچ API key موجود نیست!")
            return
        
        print("\n" + "=" * 60)
        
        # 3. تست ترجمه
        await self.test_translation()
        print("\n" + "=" * 60)
        
        # 4. تست load balancing
        await self.test_load_balancing()
        print("\n" + "=" * 60)
        
        # 5. تست performance
        await self.test_performance_comparison()
        print("\n" + "=" * 60)
        
        # 6. آمار نهایی
        await self.test_health_check()
        
        print("\n🎉 تست کامل تمام شد!")

async def main():
    """تابع اصلی"""
    print("🔥 Multi-Provider AI System Tester v2.0")
    print("📝 تست کننده سیستم چند provider با کلیدهای متعدد")
    print("-" * 50)
    
    # ایجاد و اجرای tester
    tester = MultiProviderTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ تست توسط کاربر متوقف شد")
    except Exception as e:
        print(f"\n💥 خطای کلی: {e}")
        logger.exception("خطای کلی در tester")