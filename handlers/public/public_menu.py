#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
منوی عمومی ربات و قابلیت‌های آن
شامل بخش ارزهای دیجیتال و سایر خدمات عمومی
"""

import aiohttp
import asyncio
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.logger_system import bot_logger
from handlers.ai.ai_chat_handler import GeminiChatHandler
import html
import os
from datetime import datetime

class PublicMenuManager:
    def __init__(self, db_manager):
        self.db = db_manager
        # ایجاد نمونه Gemini برای ترجمه اخبار
        self.gemini = GeminiChatHandler(db_manager=db_manager)
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی اصلی عمومی"""
        keyboard = [
            [
                InlineKeyboardButton("💰 ارزهای دیجیتال", callback_data="public_crypto"),
                InlineKeyboardButton("🤖 هوش مصنوعی", callback_data="public_ai")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_crypto_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی ارزهای دیجیتال"""
        keyboard = [
            [
                InlineKeyboardButton("📈 قیمت‌های لحظه‌ای", callback_data="crypto_prices"),
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="public_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_ai_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی هوش مصنوعی"""
        keyboard = [
            [
                InlineKeyboardButton("📰 اخبار هوش مصنوعی", callback_data="ai_news"),
            ],
            [
                InlineKeyboardButton("🔙 بازگشت", callback_data="public_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def fetch_crypto_prices(self) -> Dict[str, Any]:
        """دریافت قیمت‌های ارزهای دیجیتال از منابع مختلف"""
        try:
            result = {
                'bitcoin': {'price_usd': 0, 'change_24h': 0},
                'ethereum': {'price_usd': 0, 'change_24h': 0},
                'top_gainer': {'symbol': 'N/A', 'change_24h': 0, 'price_usd': 0},
                'top_loser': {'symbol': 'N/A', 'change_24h': 0, 'price_usd': 0},
                'tether_irr': 0,
                'tether_change_24h': 0,
                'usd_irr': 0,
                'error': None
            }
            
            async with aiohttp.ClientSession() as session:
                # دریافت قیمت‌های ارز از CoinGecko
                try:
                    crypto_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
                    async with session.get(crypto_url, timeout=10) as response:
                        if response.status == 200:
                            crypto_data = await response.json()
                            
                            # پیدا کردن بیت کوین و اتریوم
                            for coin in crypto_data:
                                if coin['id'] == 'bitcoin':
                                    result['bitcoin'] = {
                                        'price_usd': coin['current_price'],
                                        'change_24h': coin['price_change_percentage_24h']
                                    }
                                elif coin['id'] == 'ethereum':
                                    result['ethereum'] = {
                                        'price_usd': coin['current_price'],
                                        'change_24h': coin['price_change_percentage_24h']
                                    }
                            
                            # پیدا کردن بیشترین صعود و نزول
                            # فیلتر کردن ارزهای معتبر (top 50)
                            valid_coins = crypto_data[:50]
                            
                            if valid_coins:
                                # بیشترین صعود
                                top_gainer = max(valid_coins, key=lambda x: x['price_change_percentage_24h'] or 0)
                                result['top_gainer'] = {
                                    'symbol': top_gainer['symbol'].upper(),
                                    'name': top_gainer['name'],
                                    'change_24h': top_gainer['price_change_percentage_24h'],
                                    'price_usd': top_gainer['current_price']
                                }
                                
                                # بیشترین نزول
                                top_loser = min(valid_coins, key=lambda x: x['price_change_percentage_24h'] or 0)
                                result['top_loser'] = {
                                    'symbol': top_loser['symbol'].upper(),
                                    'name': top_loser['name'],
                                    'change_24h': top_loser['price_change_percentage_24h'],
                                    'price_usd': top_loser['current_price']
                                }
                except Exception as e:
                    result['error'] = f"خطا در دریافت قیمت ارزها: {str(e)}"
                
                # دریافت قیمت دلار از API رایگان ایرانی
                try:
                    usd_url = "https://api.codebazan.ir/arz/?type=arz"
                    async with session.get(usd_url, timeout=10) as response:
                        if response.status == 200:
                            arz_data = await response.json()
                            if arz_data.get('Ok') and arz_data.get('Result'):
                                for item in arz_data['Result']:
                                    if item.get('name') == 'دلار':
                                        # حذف کاما و تبدیل به عدد
                                        price_str = item.get('price', '0').replace(',', '')
                                        usd_price_irr = float(price_str)
                                        # تبدیل از ریال به تومان
                                        result['usd_irr'] = int(usd_price_irr / 10)
                                        break
                except Exception as e:
                    # fallback to approximate rate
                    result['usd_irr'] = 113000  # نرخ تقریبی بازار آزاد
                
                # دریافت قیمت تتر از تترلند
                try:
                    usdt_url = "https://api.tetherland.com/currencies"
                    async with session.get(usdt_url, timeout=10) as response:
                        if response.status == 200:
                            usdt_data = await response.json()
                            if usdt_data.get('status') == 200 and usdt_data.get('data'):
                                currencies = usdt_data['data'].get('currencies', {})
                                usdt_info = currencies.get('USDT', {})
                                if usdt_info:
                                    result['tether_irr'] = int(usdt_info.get('price', 0))
                                    result['tether_change_24h'] = float(usdt_info.get('diff24d', '0'))
                except Exception as e:
                    # fallback to approximate rate
                    result['tether_irr'] = 113000  # نرخ تقریبی
                    result['tether_change_24h'] = 0
                
                # اگر API ها کار نکردند، از نرخ‌های پیش‌فرض استفاده کن
                if result['usd_irr'] == 0:
                    result['usd_irr'] = 113000
                if result['tether_irr'] == 0:
                    result['tether_irr'] = 113000
            
            return result
            
        except Exception as e:
            return {'error': f"خطای کلی: {str(e)}"}
    
    async def fetch_crypto_news(self) -> List[Dict[str, str]]:
        """دریافت آخرین اخبار کریپتو از منابع RSS معتبر و ترجمه آنها به فارسی"""
        try:
            news_sources = [
                {
                    'name': 'CoinTelegraph',
                    'url': 'https://cointelegraph.com/rss',
                    'limit': 3
                },
                {
                    'name': 'CoinDesk', 
                    'url': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
                    'limit': 2
                }
            ]
            
            all_news = []
            
            async with aiohttp.ClientSession() as session:
                for source in news_sources:
                    try:
                        async with session.get(source['url'], timeout=15) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                news_items = self.parse_rss_feed(xml_content, source['name'], source['limit'])
                                all_news.extend(news_items)
                    except Exception as e:
                        # در صورت خرابی یک منبع، ادامه دهیم
                        continue
            
            if not all_news:
                return []
            
            # جمع‌آوری عنوان‌ها و توضیحات برای ترجمه گروهی
            titles = [news_item.get('title', '') for news_item in all_news]
            descriptions = [news_item.get('description', '') for news_item in all_news]
            
            try:
                # ترجمه گروهی عنوان‌ها در یک درخواست
                translated_titles = await self.gemini.translate_multiple_texts(titles)
                
                # ترجمه گروهی توضیحات در یک درخواست
                translated_descriptions = await self.gemini.translate_multiple_texts(descriptions)
                
                # اختصاص ترجمه‌ها به اخبار
                for i, news_item in enumerate(all_news):
                    if i < len(translated_titles):
                        news_item['title_fa'] = translated_titles[i]
                    else:
                        news_item['title_fa'] = news_item.get('title', '')
                    
                    if i < len(translated_descriptions):
                        news_item['description_fa'] = translated_descriptions[i]
                    else:
                        news_item['description_fa'] = news_item.get('description', '')
                
            except Exception as e:
                # در صورت خطا در ترجمه گروهی، متن اصلی را نگه داریم
                for news_item in all_news:
                    news_item['title_fa'] = news_item.get('title', '')
                    news_item['description_fa'] = news_item.get('description', '')
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
            
            # بازگشت حداکثر 8 خبر
            return all_news[:8]
            
        except Exception as e:
            return []
    
    def parse_rss_feed(self, xml_content: str, source_name: str, limit: int) -> List[Dict[str, str]]:
        """پارس کردن محتوای RSS و استخراج اخبار"""
        try:
            root = ET.fromstring(xml_content)
            items = root.findall('.//item')[:limit]
            
            news_list = []
            for item in items:
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
                        # حذف HTML tags
                        import re
                        desc_text = html.unescape(description_elem.text)
                        desc_text = re.sub(r'<[^>]+>', '', desc_text)
                        description = desc_text.strip()[:120] + '...' if len(desc_text) > 120 else desc_text.strip()
                    
                    # تاریخ انتشار
                    published = pub_date_elem.text if pub_date_elem is not None else ''
                    
                    news_list.append({
                        'title': title,
                        'link': link,
                        'description': description,
                        'source': source_name,
                        'published': published
                    })
            
            return news_list
            
        except Exception as e:
            return []
    
    async def fetch_ai_news(self) -> List[Dict[str, str]]:
        """دریافت آخرین اخبار هوش مصنوعی از منابع RSS معتبر با ترجمه گروهی"""
        try:
            news_sources = [
                {
                    'name': 'MIT Technology Review AI',
                    'url': 'https://feeds.feedburner.com/technology-review',
                    'limit': 4
                },
                {
                    'name': 'AI News',
                    'url': 'https://www.artificialintelligence-news.com/feed/',
                    'limit': 4
                }
            ]
            
            all_news = []
            
            async with aiohttp.ClientSession() as session:
                for source in news_sources:
                    try:
                        async with session.get(source['url'], timeout=15) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                news_items = self.parse_rss_feed(xml_content, source['name'], source['limit'])
                                all_news.extend(news_items)
                    except Exception as e:
                        continue
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
            
            # بازگشت حداکثر 8 خبر
            all_news = all_news[:8]
            
            if not all_news:
                return []
            
            # جمع‌آوری عنوان‌ها و توضیحات برای ترجمه گروهی
            titles = [news_item.get('title', '') for news_item in all_news]
            descriptions = [news_item.get('description', '') for news_item in all_news]
            
            try:
                # ترجمه گروهی عنوان‌ها در یک درخواست
                translated_titles = await self.gemini.translate_multiple_texts(titles)
                
                # ترجمه گروهی توضیحات در یک درخواست
                translated_descriptions = await self.gemini.translate_multiple_texts(descriptions)
                
                # اختصاص ترجمه‌ها به اخبار
                for i, news_item in enumerate(all_news):
                    if i < len(translated_titles):
                        news_item['title_fa'] = translated_titles[i]
                    else:
                        news_item['title_fa'] = news_item.get('title', '')
                    
                    if i < len(translated_descriptions):
                        news_item['description_fa'] = translated_descriptions[i]
                    else:
                        news_item['description_fa'] = news_item.get('description', '')
                
            except Exception as e:
                # در صورت خطا در ترجمه، از متون اصلی استفاده می‌کنیم
                for news_item in all_news:
                    news_item['title_fa'] = news_item.get('title', '')
                    news_item['description_fa'] = news_item.get('description', '')
            
            return all_news
            
        except Exception as e:
            return []

    async def fetch_general_news(self) -> List[Dict[str, str]]:
        """دریافت آخرین اخبار عمومی از منابع متعدد داخلی و خارجی با ترجمه"""
        try:
            news_sources = [
                # منابع داخلی (فارسی)
                {
                    'name': 'ایرنا',
                    'url': 'https://www.irna.ir/rss/0/5/4/news.xml',
                    'limit': 2,
                    'language': 'fa'
                },
                {
                    'name': 'خبرگزاری مهر', 
                    'url': 'https://www.mehrnews.com/rss',
                    'limit': 2,
                    'language': 'fa'
                },
                {
                    'name': 'تسنیم',
                    'url': 'https://www.tasnimnews.com/fa/rss/feed/0/8/0/%D8%A2%D8%AE%D8%B1%DB%8C%D9%86-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1',
                    'limit': 2,
                    'language': 'fa'
                },
                {
                    'name': 'فارس',
                    'url': 'https://www.farsnews.ir/rss.xml',
                    'limit': 2,
                    'language': 'fa'
                },
                # منابع خارجی (انگلیسی - نیاز به ترجمه)
                {
                    'name': 'BBC Persian',
                    'url': 'https://feeds.bbci.co.uk/news/world/rss.xml',
                    'limit': 1,
                    'language': 'en'
                },
                {
                    'name': 'Reuters World',
                    'url': 'https://feeds.reuters.com/reuters/topNews',
                    'limit': 1,
                    'language': 'en'
                },
                {
                    'name': 'AP News',
                    'url': 'https://feeds.apnews.com/topnews',
                    'limit': 1,
                    'language': 'en'
                }
            ]
            
            all_news = []
            foreign_news = []  # برای ذخیره اخبار خارجی که نیاز به ترجمه دارند
            
            async with aiohttp.ClientSession() as session:
                for source in news_sources:
                    try:
                        async with session.get(source['url'], timeout=15) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                news_items = self.parse_rss_feed(xml_content, source['name'], source['limit'])
                                
                                # اگر منبع خارجی باشد، به لیست جداگانه برای ترجمه اضافه می‌کنیم
                                if source['language'] == 'en':
                                    foreign_news.extend(news_items)
                                else:
                                    all_news.extend(news_items)
                    except Exception as e:
                        logger.warning(f"⚠️ خطا در خواندن RSS منبع {source['name']}: {e}")
                        continue
            
            # دیباگ: چاپ تعداد خبرهای دریافتی از هر منبع
            logger.info(f"📰 مجموع {len(all_news)} خبر از تمام منابع دریافت شد")
            logger.info(f"📰 {len(foreign_news)} خبر خارجی برای ترجمه آماده")
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
            
            # اگر اخبار خارجی موجود باشد، آنها را ترجمه می‌کنیم
            if foreign_news:
                try:
                    # جمع‌آوری عنوان‌ها و توضیحات برای ترجمه گروهی
                    foreign_titles = [news_item.get('title', '') for news_item in foreign_news]
                    foreign_descriptions = [news_item.get('description', '') for news_item in foreign_news]
                    
                    # ترجمه گروهی عنوان‌ها و توضیحات
                    translated_titles = await self.gemini.translate_multiple_texts(foreign_titles)
                    translated_descriptions = await self.gemini.translate_multiple_texts(foreign_descriptions)
                    
                    # اختصاص ترجمه‌ها به اخبار خارجی
                    for i, news_item in enumerate(foreign_news):
                        if i < len(translated_titles):
                            news_item['title_fa'] = translated_titles[i]
                        else:
                            news_item['title_fa'] = news_item.get('title', '')
                        
                        if i < len(translated_descriptions):
                            news_item['description_fa'] = translated_descriptions[i]
                        else:
                            news_item['description_fa'] = news_item.get('description', '')
                    
                    # اضافه کردن اخبار خارجی به لیست اصلی
                    all_news.extend(foreign_news)
                    
                except Exception as e:
                    # در صورت خطا در ترجمه، از متون اصلی استفاده می‌کنیم
                    for news_item in foreign_news:
                        news_item['title_fa'] = news_item.get('title', '')
                        news_item['description_fa'] = news_item.get('description', '')
                    all_news.extend(foreign_news)
                    
                    # لاگ کردن خطا برای debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        logger.warning("⚠️ کوئوتای Gemini API تمام شده است. متون اصلی نمایش داده می‌شوند.")
                    else:
                        logger.error(f"❌ خطا در ترجمه اخبار عمومی: {e}")
            
            # مرتب‌سازی نهایی و انتخاب 10 خبر
            all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
            all_news = all_news[:10]
            
            return all_news
            
        except Exception as e:
            return []
    
    def format_crypto_news_message(self, news_list: List[Dict[str, str]]) -> str:
        """فرمت کردن پیام اخبار کریپتو (با متن ترجمه شده به فارسی)"""
        if not news_list:
            return "❌ خطا در دریافت اخبار کریپتو. لطفاً بعداً امتحان کنید."
        
        message = "📈 *آخرین اخبار کریپتو (به فارسی)*\n\n"
        
        for i, news in enumerate(news_list, 1):
            # استفاده از متن ترجمه شده
            title_fa = news.get('title_fa', '')
            title_en = news.get('title', '')
            title = title_fa if title_fa else title_en
            
            title = title[:80] + '...' if len(title) > 80 else title
            # Escape markdown characters
            title = title.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            description_fa = news.get('description_fa', '')
            description_en = news.get('description', '')
            description = description_fa if description_fa else description_en
            
            description = description[:100] + '...' if len(description) > 100 else description
            # Escape markdown characters
            description = description.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            source_name = news.get('source', 'نامشخص')
            
            message += f"📰 *{i}. {title}*\n"
            if description:
                message += f"   {description}\n"
            message += f"   📊 منبع: {source_name}\n"
            message += f"   🔗 [ادامه مطلب]({news['link']})\n\n"
        
        message += "🤖 ترجمه شده توسط هوش مصنوعی Gemini\n"
        message += "⏰ آخرین به‌روزرسانی: همین الان"
        
        return message
    
    def format_ai_news_message(self, news_list: List[Dict[str, str]]) -> str:
        """فرمت کردن پیام اخبار هوش مصنوعی (با متن ترجمه شده به فارسی)"""
        if not news_list:
            return "❌ خطا در دریافت اخبار. لطفاً بعداً امتحان کنید."
        
        message = "🤖 *آخرین اخبار هوش مصنوعی (به فارسی)*\n\n"
        
        for i, news in enumerate(news_list, 1):
            # آیکون‌های مختلف برای منابع مختلف
            if 'MIT Technology Review' in news['source']:
                source_icon = "🧠"
            elif 'AI News' in news['source']:
                source_icon = "🤖"
            else:
                source_icon = "📰"
            
            # استفاده از متن ترجمه شده
            title = news.get('title_fa', news.get('title', ''))
            title = title[:80] + '...' if len(title) > 80 else title
            # Escape markdown characters
            title = title.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            description = news.get('description_fa', news.get('description', ''))
            description = description[:120] + '...' if len(description) > 120 else description
            # Escape markdown characters
            description = description.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            # تیتر
            message += f"{source_icon} *{i}. {title}*\n"
            
            # منبع
            message += f"📡 منبع: {news['source']}\n"
            
            # توضیحات (اگر موجود باشد)
            if description:
                message += f"📝 {description}\n"
            
            message += f"🔗 [ادامه مطلب]({news['link']})\n\n"
        
        message += "🤖 ترجمه شده توسط هوش مصنوعی Gemini\n"
        message += "⏰ آخرین به‌روزرسانی: همین الان"
        
        return message
    
    def format_general_news_message(self, news_list: List[Dict[str, str]]) -> str:
        """فرمت کردن پیام اخبار عمومی (با متن ترجمه شده به فارسی)"""
        if not news_list:
            return "❌ خطا در دریافت اخبار عمومی. لطفاً بعداً امتحان کنید."
        
        message = "📺 *آخرین اخبار روز (به فارسی)*\n\n"
        
        for i, news in enumerate(news_list, 1):
            # آیکون‌های مختلف برای منابع مختلف
            if 'تسنیم' in news['source']:
                source_icon = "📡"
            elif 'ایرنا' in news['source']:
                source_icon = "🇮🇷"
            elif 'مهر' in news['source']:
                source_icon = "🔸"
            elif 'فارس' in news['source']:
                source_icon = "⭐"
            elif 'BBC' in news['source']:
                source_icon = "🇬🇧"
            elif 'Reuters' in news['source']:
                source_icon = "🌍"
            elif 'AP' in news['source']:
                source_icon = "🇺🇸"
            else:
                source_icon = "📰"
            
            # استفاده از متن ترجمه شده (در صورت موجود بودن)
            title = news.get('title_fa', news.get('title', ''))
            title = title[:80] + '...' if len(title) > 80 else title
            # Escape markdown characters
            title = title.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            description = news.get('description_fa', news.get('description', ''))
            description = description[:100] + '...' if len(description) > 100 else description
            # Escape markdown characters
            description = description.replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)')
            
            # تیتر
            message += f"{source_icon} *{i}. {title}*\n"
            
            # منبع
            message += f"📡 منبع: {news['source']}\n"
            
            # توضیحات (اگر موجود باشد)
            if description:
                message += f"📝 {description}\n"
            
            message += f"🔗 [ادامه مطلب]({news['link']})\n\n"
        
        message += "🤖 ترجمه شده توسط هوش مصنوعی Gemini\n"
        message += "⏰ آخرین به‌روزرسانی: همین الان"
        
        return message
    
    def format_crypto_message(self, data: Dict[str, Any]) -> str:
        """فرمت کردن پیام قیمت‌های ارز"""
        if data.get('error'):
            return f"❌ خطا در دریافت اطلاعات:\n{data['error']}"
        
        # تبدیل دلار به تومان (اگر موجود باشد)
        usd_to_irr = data.get('usd_irr', 70000)  # fallback rate
        if usd_to_irr == 0:
            usd_to_irr = 70000
        
        message = "💰 *قیمت‌های لحظه‌ای ارز*\n\n"
        
        # بیت کوین
        btc = data.get('bitcoin', {})
        if btc.get('price_usd'):
            btc_irr = btc['price_usd'] * usd_to_irr
            btc_change = btc.get('change_24h', 0)
            change_icon = "🔺" if btc_change > 0 else "🔻" if btc_change < 0 else "➖"
            message += f"🟠 *بیت کوین (BTC):*\n"
            message += f"💵 ${btc['price_usd']:,.0f}\n"
            message += f"💰 {btc_irr:,.0f} تومان\n"
            message += f"{change_icon} {btc_change:+.2f}% (24 ساعت)\n\n"
        
        # اتریوم
        eth = data.get('ethereum', {})
        if eth.get('price_usd'):
            eth_irr = eth['price_usd'] * usd_to_irr
            eth_change = eth.get('change_24h', 0)
            change_icon = "🔺" if eth_change > 0 else "🔻" if eth_change < 0 else "➖"
            message += f"🔵 *اتریوم (ETH):*\n"
            message += f"💵 ${eth['price_usd']:,.0f}\n"
            message += f"💰 {eth_irr:,.0f} تومان\n"
            message += f"{change_icon} {eth_change:+.2f}% (24 ساعت)\n\n"
        
        # بیشترین صعود
        gainer = data.get('top_gainer', {})
        if gainer.get('symbol'):
            gainer_price_irr = gainer.get('price_usd', 0) * usd_to_irr
            message += f"🚀 *بیشترین صعود:*\n"
            message += f"🔥 {gainer['symbol']} ({gainer.get('name', 'N/A')})\n"
            message += f"💵 ${gainer.get('price_usd', 0):,.4f}\n"
            message += f"💰 {gainer_price_irr:,.0f} تومان\n"
            message += f"🔺 {gainer.get('change_24h', 0):+.2f}%\n\n"
        
        # بیشترین نزول
        loser = data.get('top_loser', {})
        if loser.get('symbol'):
            loser_price_irr = loser.get('price_usd', 0) * usd_to_irr
            message += f"📉 *بیشترین نزول:*\n"
            message += f"💥 {loser['symbol']} ({loser.get('name', 'N/A')})\n"
            message += f"💵 ${loser.get('price_usd', 0):,.4f}\n"
            message += f"💰 {loser_price_irr:,.0f} تومان\n"
            message += f"🔻 {loser.get('change_24h', 0):+.2f}%\n\n"
        
        # خط جداکننده
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        
        # تتر
        if data.get('tether_irr') and data['tether_irr'] > 0:
            usdt_change = data.get('tether_change_24h', 0)
            change_icon = "🔺" if usdt_change > 0 else "🔻" if usdt_change < 0 else "➖"
            message += f"🟢 *تتر (USDT):*\n"
            message += f"💰 {data['tether_irr']:,.0f} تومان\n"
            if usdt_change != 0:
                message += f"{change_icon} {usdt_change:+.2f}% (24 ساعت)\n\n"
            else:
                message += "\n"
        else:
            message += f"🟢 *تتر (USDT):* ❌ ناموجود\n\n"
        
        # دلار
        if data.get('usd_irr') and data['usd_irr'] > 0:
            message += f"💵 *دلار آمریکا (USD):*\n"
            message += f"💰 {data['usd_irr']:,.0f} تومان\n\n"
        else:
            message += f"💵 *دلار آمریکا (USD):* ❌ ناموجود\n\n"
        
        message += f"🕐 *آخرین بروزرسانی:* همین الان\n"
        message += f"📊 *منبع:* CoinGecko, تترلند, CodeBazan"
        
        return message
    
    async def show_main_menu(self, query):
        """نمایش منوی اصلی"""
        message = """
🏠 *منوی اصلی*

به ربات خوش آمدید! از دکمه زیر برای دسترسی به خدمات استفاده کنید:

💰 *ارزهای دیجیتال:* قیمت‌های لحظه‌ای ارزها، تتر و دلار
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_crypto_menu(self, query):
        """نمایش منوی ارزهای دیجیتال"""
        message = """
💰 *بخش ارزهای دیجیتال*

🔍 *خدمات موجود:*
• 📈 قیمت‌های لحظه‌ای ارزهای اصلی
• 📊 بررسی تغییرات 24 ساعته
• 💰 قیمت تتر و دلار به تومان
• 🚀 بیشترین صعود و نزول بازار
• 📰 اخبار کریپتو از کیبورد اصلی (دکمه 📈 اخبار کریپتو)

از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_crypto_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_ai_menu(self, query):
        """نمایش منوی هوش مصنوعی"""
        message = """
🤖 *بخش هوش مصنوعی*

🔍 *خدمات موجود:*
• 📰 آخرین اخبار هوش مصنوعی از منابع معتبر جهان
• 🚀 پیشرفت‌های جدید در AI و Machine Learning
• 💡 کاربردهای نوین هوش مصنوعی در صنایع مختلف
• 🔬 تحقیقات و پژوهش‌های علمی AI
• 📊 تحلیل بازار و سرمایه‌گذاری در استارتاپ‌های AI

از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_ai_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_crypto_prices(self, query):
        """نمایش قیمت‌های ارز"""
        # نمایش پیام در حال بارگذاری
        loading_message = "⏳ در حال دریافت قیمت‌های لحظه‌ای...\n\nلطفاً چند ثانیه صبر کنید."
        await query.edit_message_text(loading_message)
        
        try:
            # دریافت داده‌ها
            crypto_data = await self.fetch_crypto_prices()
            message = self.format_crypto_message(crypto_data)
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="crypto_prices")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="public_crypto")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت قیمت‌ها:\n{str(e)}"
            keyboard = [
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="crypto_prices")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="public_crypto")]
            ]
            
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    

    
    async def show_ai_news(self, query):
        """نمایش آخرین اخبار هوش مصنوعی"""
        # نمایش پیام در حال بارگذاری
        loading_message = "⏳ در حال دریافت آخرین اخبار هوش مصنوعی...\n\nلطفاً چند ثانیه صبر کنید."
        await query.edit_message_text(loading_message)
        
        try:
            # دریافت اخبار
            news_list = await self.fetch_ai_news()
            message = self.format_ai_news_message(news_list)
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="ai_news")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="public_ai")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت اخبار:\n{str(e)}"
            keyboard = [
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="ai_news")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="public_ai")]
            ]
            
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    
    async def handle_public_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت callback های منوی عمومی"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        # لاگ عملیات
        bot_logger.log_user_action(user_id, data)
        
        try:
            if data == "public_main":
                await self.show_main_menu(query)
            
            elif data == "public_crypto":
                await self.show_crypto_menu(query)
            
            elif data == "crypto_prices":
                await self.show_crypto_prices(query)
            

            
            elif data == "public_ai":
                await self.show_ai_menu(query)
            
            elif data == "ai_news":
                await self.show_ai_news(query)
            
            else:
                await query.edit_message_text("❌ دستور نامعتبر")
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در پردازش: {str(e)}")
