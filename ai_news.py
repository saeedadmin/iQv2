#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول اخبار هوش مصنوعی
دریافت آخرین اخبار AI از منابع معتبر
نویسنده: MiniMax Agent
"""

import asyncio
import aiohttp
import feedparser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# منابع خبری هوش مصنوعی
AI_NEWS_SOURCES = [
    {
        'name': 'TechCrunch AI',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'icon': '🚀'
    },
    {
        'name': 'VentureBeat AI',
        'url': 'https://venturebeat.com/category/ai/feed/',
        'icon': '📡'
    },
    {
        'name': 'The Verge AI',
        'url': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
        'icon': '🔬'
    },
    {
        'name': 'AI News',
        'url': 'https://www.artificialintelligence-news.com/feed/',
        'icon': '🤖'
    }
]

async def fetch_rss_feed(session, source):
    """دریافت یک RSS feed"""
    try:
        async with session.get(source['url'], timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                
                entries = []
                for entry in feed.entries[:3]:  # فقط 3 خبر از هر منبع
                    # تبدیل تاریخ
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.now()
                    
                    # خلاصه متن
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = entry.summary[:150] + "..." if len(entry.summary) > 150 else entry.summary
                    elif hasattr(entry, 'description'):
                        summary = entry.description[:150] + "..." if len(entry.description) > 150 else entry.description
                    
                    entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'summary': summary,
                        'pub_date': pub_date,
                        'source': source['name'],
                        'icon': source['icon']
                    })
                
                return entries
            else:
                logger.warning(f"خطا در دریافت {source['name']}: HTTP {response.status}")
                return []
                
    except Exception as e:
        logger.error(f"خطا در دریافت اخبار از {source['name']}: {e}")
        return []

async def get_ai_news():
    """دریافت آخرین اخبار هوش مصنوعی"""
    try:
        all_entries = []
        
        # دریافت اخبار از تمام منابع
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_rss_feed(session, source) for source in AI_NEWS_SOURCES]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_entries.extend(result)
        
        if not all_entries:
            return "❌ متاسفانه در حال حاضر امکان دریافت اخبار وجود ندارد."
        
        # مرتب‌سازی بر اساس تاریخ انتشار
        all_entries.sort(key=lambda x: x['pub_date'], reverse=True)
        
        # انتخاب 8 خبر جدیدترین
        latest_entries = all_entries[:8]
        
        # فرمت‌بندی پیام
        formatted_news = "🤖 **آخرین اخبار هوش مصنوعی**\n\n"
        
        for i, entry in enumerate(latest_entries, 1):
            # حذف تگ‌های HTML از عنوان و خلاصه
            title = entry['title'].replace('<', '&lt;').replace('>', '&gt;')
            summary = entry['summary'].replace('<', '&lt;').replace('>', '&gt;')
            
            formatted_news += f"{entry['icon']} **[{title}]({entry['link']})**\n"
            formatted_news += f"📡 منبع: {entry['source']}\n"
            
            if summary:
                formatted_news += f"📝 {summary}\n"
            
            # فاصله بین اخبار
            if i < len(latest_entries):
                formatted_news += "\n"
        
        # اضافه کردن footer
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        formatted_news += f"\n⏰ آخرین بروزرسانی: {current_time}\n"
        formatted_news += f"📊 تعداد منابع: {len(AI_NEWS_SOURCES)} | تعداد اخبار: {len(latest_entries)}"
        
        return formatted_news
        
    except Exception as e:
        logger.error(f"خطا در دریافت اخبار هوش مصنوعی: {e}")
        return f"❌ خطا در دریافت اخبار: {str(e)}"

# تست فانکشن
async def test_ai_news():
    """تست دریافت اخبار"""
    print("در حال دریافت اخبار هوش مصنوعی...")
    news = await get_ai_news()
    print(news)

if __name__ == "__main__":
    asyncio.run(test_ai_news())
