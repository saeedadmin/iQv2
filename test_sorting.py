#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست برای بررسی مرتب‌سازی محبوب‌ترین vs جدیدترین
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_sorting_difference():
    """تست تفاوت بین محبوب‌ترین و جدیدترین"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    symbol = "BTCUSDT"
    
    # URL برای محبوب‌ترین (بدون پارامتر)
    popular_url = f"https://www.tradingview.com/symbols/{symbol}/ideas/"
    
    # URL برای جدیدترین (با پارامتر sort=recent)
    recent_url = f"https://www.tradingview.com/symbols/{symbol}/ideas/?sort=recent"
    
    print("🔥 تست محبوب‌ترین تحلیل‌ها:")
    popular_links = await get_first_analysis_links(popular_url, headers)
    
    print("\n" + "="*50)
    print("🕐 تست جدیدترین تحلیل‌ها:")
    recent_links = await get_first_analysis_links(recent_url, headers)
    
    print("\n" + "="*50)
    print("📊 مقایسه نتایج:")
    
    if popular_links and recent_links:
        if popular_links[0] == recent_links[0]:
            print("❌ مشکل: اولین لینک محبوب‌ترین و جدیدترین یکسان است!")
            print(f"   لینک یکسان: {popular_links[0]}")
        else:
            print("✅ عالی: لینک‌های محبوب‌ترین و جدیدترین متفاوت هستند")
            print(f"   محبوب‌ترین: {popular_links[0]}")
            print(f"   جدیدترین: {recent_links[0]}")
    
    print(f"\n🔗 تعداد لینک‌های محبوب‌ترین: {len(popular_links) if popular_links else 0}")
    print(f"🔗 تعداد لینک‌های جدیدترین: {len(recent_links) if recent_links else 0}")

async def get_first_analysis_links(url, headers, max_links=3):
    """دریافت اولین چند لینک تحلیل از URL"""
    
    print(f"🔍 URL: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    idea_links = soup.find_all('a', href=True)
                    processed_urls = set()
                    found_links = []
                    
                    for link in idea_links:
                        href = link.get('href', '')
                        
                        # منطق فعلی ما
                        if ('/chart/' in href and 
                            '/' in href.split('/chart/')[-1] and 
                            any(char.isalnum() for char in href) and 
                            len(href.split('/chart/')[-1]) > 10 and
                            '-' in href.split('/chart/')[-1] and
                            '#chart-view-comment-form' not in href):
                            
                            clean_href = href.split('#')[0]
                            analysis_url = clean_href if clean_href.startswith('http') else f"https://www.tradingview.com{clean_href}"
                            
                            if analysis_url not in processed_urls:
                                processed_urls.add(analysis_url)
                                found_links.append(analysis_url)
                                
                                if len(found_links) <= max_links:
                                    print(f"  {len(found_links)}. {analysis_url}")
                                
                                if len(found_links) >= max_links:
                                    break
                    
                    return found_links
                
                else:
                    print(f"❌ خطای HTTP: {response.status}")
                    return []
                    
    except Exception as e:
        print(f"❌ خطا: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(test_sorting_difference())