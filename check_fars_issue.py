#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
بررسی مشکل منبع فارس و پیدا کردن جایگزین مناسب
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_fars_issue():
    """بررسی مشکل منبع فارس"""
    url = "https://www.farsnews.ir/rss.xml"
    
    logger.info("🔍 بررسی مشکل منبع فارس...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                content = await response.text()
                logger.info(f"📏 طول محتوا: {len(content)} کاراکتر")
                logger.info(f"🔗 URL: {response.url}")
                logger.info(f"📡 Status: {response.status}")
                
                # نمایش بخشی از محتوا برای debug
                lines = content.split('\n')
                logger.info(f"📄 تعداد خطوط: {len(lines)}")
                logger.info("🔍 اولین 10 خط:")
                for i, line in enumerate(lines[:10]):
                    logger.info(f"  {i+1}: {line[:100]}...")
                
                # جستجوی خطاهای XML
                if "mismatched tag" in content:
                    logger.error("❌ خطای XML mismatched tag پیدا شد")
                
                if "<html" in content.lower():
                    logger.error("❌ به نظر می‌رسد به HTML redirect شده، نه RSS")
                
    except Exception as e:
        logger.error(f"❌ خطا: {e}")

async def find_replacement_source():
    """پیدا کردن منبع جایگزین برای فارس"""
    alternatives = [
        {
            'name': 'ایرنا (IRNA) - جایگزین فارس',
            'url': 'https://www.irna.ir/rss/fa/1',
            'limit': 2
        },
        {
            'name': 'ایرنا سیاسی',
            'url': 'https://www.irna.ir/rss/fa/3',
            'limit': 2
        },
        {
            'name': 'برنا خبرگزاری',
            'url': 'https://www.borna.news/rss',
            'limit': 2
        },
        {
            'name': 'مهر عمومی',
            'url': 'https://www.mehrnews.com/rss/tp/1',
            'limit': 2
        },
        {
            'name': 'تسنیم عمومی',
            'url': 'https://www.tasnimnews.com/fa/rss/feed/0/110/0',
            'limit': 2
        }
    ]
    
    logger.info("🔍 تست منابع جایگزین...")
    
    working_sources = []
    
    for source in alternatives:
        logger.info(f"\n🔍 تست: {source['name']}")
        logger.info(f"🔗 URL: {source['url']}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source['url'], timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 1000:  # حداقل محتوای معتبر
                            logger.info(f"✅ موفق - {len(content)} کاراکتر")
                            working_sources.append(source)
                        else:
                            logger.warning(f"⚠️ محتوای کم - {len(content)} کاراکتر")
                    else:
                        logger.error(f"❌ HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ خطا: {e}")
    
    logger.info(f"\n📊 منابع جایگزین کارکرده:")
    for source in working_sources:
        logger.info(f"  ✅ {source['name']}")
    
    return working_sources

async def main():
    await check_fars_issue()
    await find_replacement_source()

if __name__ == "__main__":
    asyncio.run(main())