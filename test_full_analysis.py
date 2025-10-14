#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست کامل سیستم تحلیل TradingView برای یافتن مشکل لینک‌ها
"""

import asyncio
from tradingview_analysis import TradingViewAnalysisFetcher

async def test_full_analysis():
    """تست کامل سیستم تحلیل"""
    
    print("🧪 شروع تست کامل سیستم تحلیل TradingView")
    print("="*60)
    
    # ایجاد instance از fetcher
    fetcher = TradingViewAnalysisFetcher()
    
    # تست با BTCUSDT
    crypto_pair = "btcusdt"
    print(f"💰 تست برای: {crypto_pair.upper()}")
    
    # تست individual scrapers اول
    print("\n🔍 تست جداگانه محبوب‌ترین:")
    popular_data = await fetcher.scrape_community_analysis(crypto_pair.upper(), "popular")
    if popular_data:
        print(f"  ✅ عنوان: {popular_data['title'][:50]}...")
        print(f"  🔗 لینک: {popular_data['analysis_url']}")
    else:
        print("  ❌ خطا در دریافت محبوب‌ترین")
    
    print("\n🕐 تست جداگانه جدیدترین:")
    recent_data = await fetcher.scrape_community_analysis(crypto_pair.upper(), "recent")
    if recent_data:
        print(f"  ✅ عنوان: {recent_data['title'][:50]}...")
        print(f"  🔗 لینک: {recent_data['analysis_url']}")
    else:
        print("  ❌ خطا در دریافت جدیدترین")
    
    print("\n" + "="*60)
    print("📊 تست تابع اصلی fetch_latest_analysis:")
    
    # تست تابع اصلی
    analysis_result = await fetcher.fetch_latest_analysis(crypto_pair)
    
    if analysis_result.get('success'):
        print("✅ تحلیل با موفقیت دریافت شد")
        
        # بررسی اینکه آیا دو تحلیل داریم یا یکی
        if 'popular_analysis' in analysis_result and 'recent_analysis' in analysis_result:
            print("\n🎯 دو تحلیل دریافت شده:")
            
            popular = analysis_result['popular_analysis']
            recent = analysis_result['recent_analysis']
            
            print(f"\n🔥 محبوب‌ترین:")
            print(f"   عنوان: {popular['title'][:60]}...")
            print(f"   لینک: {popular['analysis_url']}")
            
            print(f"\n🕐 جدیدترین:")
            print(f"   عنوان: {recent['title'][:60]}...")
            print(f"   لینک: {recent['analysis_url']}")
            
            # بررسی تکراری بودن
            if popular['analysis_url'] == recent['analysis_url']:
                print("\n❌ مشکل: لینک‌های محبوب‌ترین و جدیدترین یکسان هستند!")
            else:
                print("\n✅ عالی: لینک‌ها متفاوت هستند")
                
        else:
            print("📝 فقط یک تحلیل دریافت شده:")
            print(f"   عنوان: {analysis_result.get('title', 'N/A')[:60]}...")
            print(f"   لینک: {analysis_result.get('analysis_url', 'N/A')}")
    else:
        print("❌ خطا در دریافت تحلیل:")
        print(f"   {analysis_result.get('error', 'خطای نامشخص')}")

if __name__ == "__main__":
    asyncio.run(test_full_analysis())