#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست سیستم بهبود یافته TradingView
"""

import asyncio
from tradingview_analysis import TradingViewAnalysisFetcher

async def test_improved_system():
    """تست سیستم بهبود یافته"""
    
    print("🚀 تست سیستم بهبود یافته TradingView")
    print("="*60)
    
    # ایجاد fetcher
    fetcher = TradingViewAnalysisFetcher()
    
    # تست با چندین ارز
    test_pairs = ["btcusdt", "ethusdt"]
    
    for crypto_pair in test_pairs:
        print(f"\n💰 تست {crypto_pair.upper()}:")
        print("-" * 40)
        
        # تست تابع اصلی
        analysis_result = await fetcher.fetch_latest_analysis(crypto_pair)
        
        if analysis_result.get('success'):
            if 'popular_analysis' in analysis_result and 'recent_analysis' in analysis_result:
                popular = analysis_result['popular_analysis']
                recent = analysis_result['recent_analysis']
                
                print(f"🔥 محبوب‌ترین:")
                print(f"   {popular['title'][:50]}...")
                print(f"   {popular['analysis_url']}")
                
                print(f"\n🕐 جدیدترین:")
                print(f"   {recent['title'][:50]}...")
                print(f"   {recent['analysis_url']}")
                
                # بررسی تکراری بودن
                if popular['analysis_url'] == recent['analysis_url']:
                    print(f"\n❌ هنوز مشکل دارد: لینک‌ها یکسان هستند")
                else:
                    print(f"\n✅ عالی: لینک‌ها متفاوت هستند")
                    
                # نمایش تعداد URL های استفاده شده
                print(f"\n📊 تعداد URL های ثبت شده: {len(fetcher.global_used_urls)}")
                
            else:
                print("📝 فقط یک تحلیل دریافت شده")
        else:
            print(f"❌ خطا: {analysis_result.get('error', 'نامشخص')}")
        
        print(f"\n" + "="*60)

async def test_duplicate_detection():
    """تست شناسایی و جلوگیری از تکرار"""
    
    print("\n🔍 تست ویژه برای شناسایی تکرار:")
    print("="*50)
    
    fetcher = TradingViewAnalysisFetcher()
    
    # چندین درخواست متوالی برای دیدن اینکه آیا تکرار رخ می‌دهد
    for i in range(3):
        print(f"\n📍 درخواست {i+1}:")
        
        analysis_result = await fetcher.fetch_latest_analysis("btcusdt")
        
        if analysis_result.get('success') and 'popular_analysis' in analysis_result:
            popular_url = analysis_result['popular_analysis']['analysis_url']
            recent_url = analysis_result['recent_analysis']['analysis_url']
            
            print(f"   محبوب‌ترین: ...{popular_url[-30:]}")
            print(f"   جدیدترین: ...{recent_url[-30:]}")
            
            if popular_url == recent_url:
                print("   ❌ تکرار شناسایی شد!")
            else:
                print("   ✅ لینک‌ها متفاوت")
        
        # کمی استراحت بین درخواست‌ها
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_improved_system())
    asyncio.run(test_duplicate_detection())