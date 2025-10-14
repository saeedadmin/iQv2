#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست برای بررسی لینک‌های فعلی TradingView
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_current_links():
    """تست لینک‌های فعلی که دریافت می‌کنیم"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # تست با BTCUSDT
    symbol = "BTCUSDT"
    search_url = f"https://www.tradingview.com/symbols/{symbol}/ideas/"
    
    print(f"🔍 تست URL: {search_url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    print("🔎 جستجو برای لینک‌های /chart/...")
                    
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
                                
                                # نمایش اولین 5 لینک
                                if len(found_links) <= 5:
                                    print(f"✅ لینک {len(found_links)}: {analysis_url}")
                    
                    print(f"\n📊 تعداد کل لینک‌های پیدا شده: {len(found_links)}")
                    
                    if found_links:
                        print(f"\n🎯 اولین لینک برای تست: {found_links[0]}")
                        
                        # تست کردن اولین لینک برای دیدن اینکه redirect می‌شه یا نه
                        print("\n🔍 تست اولین لینک...")
                        await test_link_redirect(session, found_links[0])
                    
                else:
                    print(f"❌ خطای HTTP: {response.status}")
                    
    except Exception as e:
        print(f"❌ خطا: {e}")

async def test_link_redirect(session, link):
    """تست کردن اینکه لینک به کجا redirect می‌شه"""
    try:
        print(f"📍 درحال تست: {link}")
        
        async with session.get(link, allow_redirects=True) as response:
            final_url = str(response.url)
            print(f"🎯 URL نهایی: {final_url}")
            
            if final_url != link:
                print("🔄 Redirect شده!")
            else:
                print("✅ Direct link")
                
            # بررسی محتوا برای یافتن canonical URL
            if response.status == 200:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # جستجو برای canonical link
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    canonical_url = canonical['href']
                    print(f"🔗 Canonical URL: {canonical_url}")
                
                # جستجو برای og:url
                og_url = soup.find('meta', property='og:url')
                if og_url and og_url.get('content'):
                    og_url_content = og_url['content']
                    print(f"📱 OG URL: {og_url_content}")
                    
    except Exception as e:
        print(f"❌ خطا در تست لینک: {e}")

if __name__ == "__main__":
    asyncio.run(test_current_links())