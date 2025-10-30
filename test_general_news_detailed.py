#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت تست دقیق برای عیب‌یابی مشکل اخبار عمومی
"""

import asyncio
import logging
import aiohttp
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime

# تنظیم لاگ برای debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/news_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DetailedNewsFetcher:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_single_rss_feed(self, source_name, url, limit=2, timeout=15):
        """تست یک منبع RSS به تنهایی"""
        logger.info(f"🔍 تست منبع: {source_name}")
        logger.info(f"🔗 URL: {url}")
        
        try:
            async with self.session.get(url, timeout=timeout) as response:
                logger.info(f"📡 وضعیت پاسخ: {response.status}")
                
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"📏 طول محتوا: {len(content)} کاراکتر")
                    
                    # پارس کردن XML
                    try:
                        root = ET.fromstring(content)
                        items = root.findall('.//item')
                        logger.info(f"📰 تعداد item های پیدا شده: {len(items)}")
                        
                        news_items = []
                        for i, item in enumerate(items[:limit]):
                            try:
                                title_elem = item.find('title')
                                link_elem = item.find('link')
                                description_elem = item.find('description')
                                pub_date_elem = item.find('pubDate')
                                
                                if title_elem is not None and link_elem is not None:
                                    title = html.unescape(title_elem.text or '').strip()
                                    link = link_elem.text or ''
                                    
                                    # پاک‌سازی توضیحات
                                    description = ''
                                    if description_elem is not None and description_elem.text:
                                        desc_text = html.unescape(description_elem.text)
                                        desc_text = re.sub(r'<[^>]+>', '', desc_text)
                                        description = desc_text.strip()[:120] + '...' if len(desc_text) > 120 else desc_text.strip()
                                    
                                    # تاریخ انتشار
                                    published = pub_date_elem.text if pub_date_elem is not None else ''
                                    
                                    news_items.append({
                                        'title': title,
                                        'link': link,
                                        'description': description,
                                        'source': source_name,
                                        'published': published
                                    })
                                    
                                    logger.info(f"  📝 خبر {i+1}: {title[:50]}...")
                                
                            except Exception as e:
                                logger.error(f"  ❌ خطا در پردازش item {i+1}: {e}")
                        
                        logger.info(f"✅ منبع {source_name}: {len(news_items)} خبر استخراج شد")
                        return news_items
                        
                    except ET.ParseError as e:
                        logger.error(f"❌ خطا در پارس XML: {e}")
                        return []
                        
                else:
                    logger.error(f"❌ خطا در دریافت پاسخ: HTTP {response.status}")
                    return []
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ timeout در دریافت پاسخ از {source_name}")
            return []
        except Exception as e:
            logger.error(f"❌ خطای کلی در {source_name}: {e}")
            return []
    
    async def test_all_news_sources(self):
        """تست تمام منابع خبری"""
        news_sources = [
            # منابع داخلی (فارسی) - منابع جدید با limit افزایش یافته
            {
                'name': 'خبرگزاری مهر', 
                'url': 'https://www.mehrnews.com/rss',
                'limit': 3,
                'language': 'fa'
            },
            {
                'name': 'تسنیم',
                'url': 'https://www.tasnimnews.com/fa/rss/feed/0/8/0/%D8%A2%D8%AE%D8%B1%DB%8C%D9%86-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1',
                'limit': 3,
                'language': 'fa'
            },
            {
                'name': 'مهر عمومی',  # جایگزین فارس خراب
                'url': 'https://www.mehrnews.com/rss/tp/1',
                'limit': 3,
                'language': 'fa'
            },
            {
                'name': 'مهر - سیاسی',
                'url': 'https://www.mehrnews.com/rss/tp/sch',
                'limit': 2,
                'language': 'fa'
            },
            {
                'name': 'تسنیم - بین‌الملل',
                'url': 'https://www.tasnimnews.com/fa/rss/feed/0/9/0/%D8%A8%DB%8C%D9%86-%D8%A7%D9%84%D9%85%D9%84%D9%84%D9%84',
                'limit': 2,
                'language': 'fa'
            },
            # منابع خارجی (انگلیسی - نیاز به ترجمه)
            {
                'name': 'BBC World',
                'url': 'https://feeds.bbci.co.uk/news/world/rss.xml',
                'limit': 2,
                'language': 'en'
            },
            {
                'name': 'CNN World',
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'limit': 2,
                'language': 'en'
            }
        ]
        
        all_news = []
        failed_sources = []
        
        logger.info("🚀 شروع تست تمام منابع خبری...")
        logger.info(f"📊 تعداد کل منابع: {len(news_sources)}")
        
        for i, source in enumerate(news_sources, 1):
            logger.info(f"\n🔍 منبع {i}/{len(news_sources)}: {source['name']}")
            
            news_items = await self.test_single_rss_feed(
                source['name'], 
                source['url'], 
                source['limit']
            )
            
            if news_items:
                all_news.extend(news_items)
                logger.info(f"✅ موفقیت: {len(news_items)} خبر")
            else:
                failed_sources.append(source['name'])
                logger.error(f"❌ شکست: هیچ خبری دریافت نشد")
        
        # خلاصه نتایج
        logger.info("\n" + "="*60)
        logger.info("📊 خلاصه نتایج تست:")
        logger.info(f"✅ منابع موفق: {len(news_sources) - len(failed_sources)}")
        logger.info(f"❌ منابع ناموفق: {len(failed_sources)}")
        logger.info(f"📰 مجموع اخبار دریافتی: {len(all_news)}")
        
        if failed_sources:
            logger.info("❌ منابع ناموفق:")
            for failed in failed_sources:
                logger.info(f"  - {failed}")
        
        if all_news:
            logger.info("\n📰 نمونه اخبار دریافتی:")
            for i, news in enumerate(all_news[:3], 1):
                logger.info(f"  {i}. {news['source']}: {news['title'][:60]}...")
        
        return all_news, failed_sources
    
    async def test_specific_issue(self):
        """تست مشکل خاص گزارش شده"""
        logger.info("\n" + "="*80)
        logger.info("🎯 تست مشکل خاص گزارش شده...")
        logger.info("مشکل: 'فقط 5 تا خبر دریافت میکنم اونم بررسی کن که 10 تا بشه'")
        logger.info("="*80)
        
        all_news, failed_sources = await self.test_all_news_sources()
        
        logger.info(f"\n🎯 نتیجه نهایی:")
        logger.info(f"📊 تعداد اخبار دریافتی: {len(all_news)}")
        logger.info(f"🎯 هدف: 10+ اخبار")
        
        if len(all_news) < 10:
            logger.error(f"❌ مشکل تأیید شد: فقط {len(all_news)} خبر دریافت شده")
            logger.error("🔍 علل احتمالی:")
            logger.error("  1. برخی منابع RSS کار نمی‌کنند")
            logger.error("  2. محدودیت تعداد خبر در هر منبع کم است")
            logger.error("  3. خطا در پردازش XML")
        else:
            logger.info(f"✅ مشکل حل شده: {len(all_news)} خبر دریافت شده")
        
        return len(all_news), failed_sources

async def main():
    """تست اصلی"""
    logger.info("🔧 شروع عیب‌یابی دقیق اخبار عمومی...")
    logger.info(f"🕐 زمان شروع: {datetime.now()}")
    
    async with DetailedNewsFetcher() as fetcher:
        try:
            news_count, failed_sources = await fetcher.test_specific_issue()
            
            logger.info(f"\n🏁 نتیجه نهایی:")
            logger.info(f"📰 تعداد اخبار: {news_count}")
            logger.info(f"❌ منابع خراب: {len(failed_sources)}")
            
            if failed_sources:
                logger.info("\n🔧 پیشنهادات برای حل مشکل:")
                for failed in failed_sources:
                    logger.info(f"  - بررسی منبع: {failed}")
            
            logger.info(f"\n🕐 زمان پایان: {datetime.now()}")
            
        except Exception as e:
            logger.error(f"❌ خطای کلی در تست: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())