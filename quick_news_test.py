#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت تست سریع برای بررسی عملکرد اخبار عمومی
استفاده: python quick_news_test.py

این اسکریپت مستقل از dependencies خارجی کار می‌کند
"""

import asyncio
import logging
import aiohttp
import xml.etree.ElementTree as ET
import html
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def fetch_general_news_quick():
    """نسخه ساده شده fetch_general_news برای تست"""
    news_sources = [
        {'name': 'خبرگزاری مهر', 'url': 'https://www.mehrnews.com/rss', 'limit': 3},
        {'name': 'تسنیم', 'url': 'https://www.tasnimnews.com/fa/rss/feed/0/8/0/%D8%A2%D8%AE%D8%B1%DB%8C%D9%86-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1', 'limit': 3},
        {'name': 'مهر عمومی', 'url': 'https://www.mehrnews.com/rss/tp/1', 'limit': 3},
        {'name': 'مهر - سیاسی', 'url': 'https://www.mehrnews.com/rss/tp/sch', 'limit': 2},
        {'name': 'تسنیم - بین‌الملل', 'url': 'https://www.tasnimnews.com/fa/rss/feed/0/9/0/%D8%A8%DB%8C%D9%86-%D8%A7%D9%84%D9%85%D9%84%D9%84%D9%84', 'limit': 2},
        {'name': 'BBC World', 'url': 'https://feeds.bbci.co.uk/news/world/rss.xml', 'limit': 2},
        {'name': 'CNN World', 'url': 'http://rss.cnn.com/rss/edition.rss', 'limit': 2}
    ]
    
    all_news = []
    
    async with aiohttp.ClientSession() as session:
        for source in news_sources:
            try:
                async with session.get(source['url'], timeout=15) as response:
                    if response.status == 200:
                        content = await response.text()
                        root = ET.fromstring(content)
                        items = root.findall('.//item')[:source['limit']]
                        
                        for item in items:
                            title_elem = item.find('title')
                            link_elem = item.find('link')
                            
                            if title_elem is not None and link_elem is not None:
                                title = html.unescape(title_elem.text or '').strip()
                                link = link_elem.text or ''
                                
                                all_news.append({
                                    'title': title,
                                    'link': link,
                                    'source': source['name']
                                })
            except:
                continue
    
    return all_news

async def quick_test():
    """تست سریع عملکرد اخبار عمومی"""
    logger.info("🚀 شروع تست سریع اخبار عمومی...")
    logger.info("📡 در حال دریافت اخبار از منابع...")
    
    try:
        news_list = await fetch_general_news_quick()
        
        logger.info(f"📊 نتیجه:")
        logger.info(f"📰 تعداد اخبار دریافتی: {len(news_list)}")
        
        if len(news_list) >= 10:
            logger.info("✅ موفقیت: تعداد اخبار کافی است")
        else:
            logger.warning(f"⚠️ هشدار: فقط {len(news_list)} خبر دریافت شد")
        
        # نمایش خلاصه منابع
        sources = {}
        for news in news_list:
            source = news.get('source', 'نامشخص')
            sources[source] = sources.get(source, 0) + 1
        
        logger.info("\n📡 خلاصه منابع:")
        for source, count in sources.items():
            logger.info(f"  • {source}: {count} خبر")
        
        # نمایش نمونه اولین خبر
        if news_list:
            first_news = news_list[0]
            logger.info(f"\n📝 نمونه اولین خبر:")
            logger.info(f"  منبع: {first_news.get('source')}")
            logger.info(f"  عنوان: {first_news.get('title', '')[:60]}...")
        
        return len(news_list) >= 10
        
    except Exception as e:
        logger.error(f"❌ خطا در تست: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(quick_test())
    if result:
        logger.info("\n🎉 تست با موفقیت انجام شد!")
        logger.info("✅ بخش اخبار عمومی آماده است")
    else:
        logger.info("\n⚠️ تست نیاز به بررسی دارد!")
        logger.info("🔧 ممکن است نیاز به عیب‌یابی بیشتر باشد")