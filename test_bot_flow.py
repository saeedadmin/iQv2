#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست flow دقیق telegram bot برای شبیه‌سازی مشکل گزارش شده
"""

import asyncio
from tradingview_analysis import TradingViewAnalysisFetcher

async def simulate_bot_request(crypto_pair):
    """شبیه‌سازی درخواست telegram bot"""
    
    print(f"🤖 شبیه‌سازی درخواست bot برای: {crypto_pair}")
    print("="*50)
    
    # ایجاد fetcher (مانند telegram bot)
    fetcher = TradingViewAnalysisFetcher()
    
    # اعتبارسنجی فرمت (مانند telegram bot)
    if not fetcher.validate_crypto_pair_format(crypto_pair):
        print("❌ فرمت نامعتبر")
        return
    
    print("✅ فرمت معتبر")
    
    # دریافت تحلیل (مانند telegram bot)
    print("⏳ در حال دریافت تحلیل...")
    analysis_data = await fetcher.fetch_latest_analysis(crypto_pair)
    
    if analysis_data.get('success'):
        print("✅ تحلیل دریافت شد")
        
        # بررسی نوع تحلیل (مانند telegram bot)
        if 'popular_analysis' in analysis_data and 'recent_analysis' in analysis_data:
            print("\n📊 دو تحلیل موجود است:")
            
            popular = analysis_data['popular_analysis']
            recent = analysis_data['recent_analysis']
            
            print(f"\n🔥 محبوب‌ترین:")
            print(f"   📝 عنوان: {popular['title']}")
            print(f"   🔗 لینک: {popular['analysis_url']}")
            print(f"   👤 نویسنده: {popular['author']}")
            print(f"   🖼️ عکس: {popular.get('image_url', 'None')}")
            
            print(f"\n🕐 جدیدترین:")
            print(f"   📝 عنوان: {recent['title']}")
            print(f"   🔗 لینک: {recent['analysis_url']}")
            print(f"   👤 نویسنده: {recent['author']}")
            print(f"   🖼️ عکس: {recent.get('image_url', 'None')}")
            
            # چک کردن مشکل کاربر
            if popular['analysis_url'] == recent['analysis_url']:
                print("\n❌❌❌ مشکل تأیید شد: لینک‌ها یکسان هستند!")
                print("🔧 نیاز به رفع مشکل")
                
                # نمایش جزئیات برای debug
                print("\n🔍 جزئیات debug:")
                print(f"   URL محبوب‌ترین: {popular['analysis_url']}")
                print(f"   URL جدیدترین: {recent['analysis_url']}")
                
                # بررسی منبع داده‌ها
                print(f"   نوع محبوب‌ترین: {popular.get('sort_type', 'نامشخص')}")
                print(f"   نوع جدیدترین: {recent.get('sort_type', 'نامشخص')}")
                
            else:
                print("\n✅ لینک‌ها متفاوت هستند - مشکل وجود ندارد!")
                
            # تست کردن لینک‌ها برای اطمینان از صحت
            print("\n🔗 تست لینک‌ها:")
            await test_link_validity(popular['analysis_url'], "محبوب‌ترین")
            await test_link_validity(recent['analysis_url'], "جدیدترین")
            
        else:
            print("📝 فقط یک تحلیل دریافت شده")
            print(f"   لینک: {analysis_data.get('analysis_url', 'N/A')}")
    else:
        print("❌ خطا در دریافت تحلیل:")
        print(f"   {analysis_data.get('error', 'خطای نامشخص')}")

async def test_link_validity(url, name):
    """تست اعتبار لینک"""
    try:
        import aiohttp
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.head(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    print(f"   ✅ {name}: وضعیت {response.status} - معتبر")
                else:
                    print(f"   ⚠️ {name}: وضعیت {response.status} - مشکوک")
    except Exception as e:
        print(f"   ❌ {name}: خطا در تست - {e}")

async def main():
    """تست‌های مختلف"""
    
    test_pairs = ["btcusdt", "ethusdt", "solusdt"]
    
    for pair in test_pairs:
        await simulate_bot_request(pair)
        print("\n" + "="*70 + "\n")
        await asyncio.sleep(2)  # فاصله بین درخواست‌ها

if __name__ == "__main__":
    asyncio.run(main())