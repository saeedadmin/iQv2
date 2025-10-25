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
from logger_system import bot_logger
import html
from datetime import datetime

class PublicMenuManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
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
                InlineKeyboardButton("📰 اخبار کریپتو", callback_data="crypto_news"),
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
        """دریافت آخرین اخبار کریپتو از منابع RSS معتبر"""
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
        """دریافت آخرین اخبار هوش مصنوعی از منابع RSS معتبر"""
        try:
            news_sources = [
                {
                    'name': 'TechCrunch AI',
                    'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
                    'limit': 3
                },
                {
                    'name': 'The Verge AI', 
                    'url': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml',
                    'limit': 2
                },
                {
                    'name': 'VentureBeat AI',
                    'url': 'https://venturebeat.com/ai/feed/',
                    'limit': 3
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
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
            
            # بازگشت حداکثر 8 خبر
            return all_news[:8]
            
        except Exception as e:
            return []
    
    def format_crypto_news_message(self, news_list: List[Dict[str, str]]) -> str:
        """فرمت کردن پیام اخبار کریپتو"""
        if not news_list:
            return "❌ خطا در دریافت اخبار. لطفاً بعداً امتحان کنید."
        
        message = "📰 *آخرین اخبار کریپتو*\n\n"
        
        for i, news in enumerate(news_list, 1):
            # آیکون‌های مختلف برای منابع مختلف
            source_icon = "🔹" if news['source'] == 'CoinTelegraph' else "🔸"
            
            # تیتر با لینک کلیک‌پذیر
            message += f"{source_icon} [{news['title']}]({news['link']})\n"
            
            # منبع
            message += f"📡 *منبع:* {news['source']}\n"
            
            # توضیحات (اگر موجود باشد)
            if news.get('description'):
                message += f"📝 {news['description']}\n"
            
            message += "\n"
        
        message += "🕐 *آخرین بروزرسانی:* همین الان\n"
        message += "📊 *منابع:* CoinTelegraph, CoinDesk"
        
        return message
    
    def format_ai_news_message(self, news_list: List[Dict[str, str]]) -> str:
        """فرمت کردن پیام اخبار هوش مصنوعی"""
        if not news_list:
            return "❌ خطا در دریافت اخبار. لطفاً بعداً امتحان کنید."
        
        message = "🤖 *آخرین اخبار هوش مصنوعی*\n\n"
        
        for i, news in enumerate(news_list, 1):
            # آیکون‌های مختلف برای منابع مختلف
            if news['source'] == 'TechCrunch AI':
                source_icon = "🔥"
            elif news['source'] == 'The Verge AI':
                source_icon = "⚡"
            elif news['source'] == 'VentureBeat AI':
                source_icon = "🚀"
            else:
                source_icon = "🤖"
            
            # تیتر با لینک کلیک‌پذیر
            message += f"{source_icon} [{news['title']}]({news['link']})\n"
            
            # منبع
            message += f"📡 *منبع:* {news['source']}\n"
            
            # توضیحات (اگر موجود باشد)
            if news.get('description'):
                message += f"📝 {news['description']}\n"
            
            message += "\n"
        
        message += "🕐 *آخرین بروزرسانی:* همین الان\n"
        message += "📊 *منابع:* TechCrunch AI, The Verge AI, VentureBeat AI"
        
        return message
    
    def format_crypto_message(self, data: Dict[str, Any]) -> str:
        """فرمت کردن پیام قیمت‌های ارز - نسخه بدون مشکل کاراکتر"""
        if data.get('error'):
            return f"❌ خطا در دریافت اطلاعات:\n{data['error']}"
        
        # تبدیل دلار به تومان
        usd_to_irr = data.get('usd_irr', 70000)
        if usd_to_irr == 0:
            usd_to_irr = 70000
        
        # آماده سازی متغیرهای پیام
        message_parts = []
        
        # هدر اصلی
        message_parts.append("💰 قیمتهای لحظه ای ارز")
        message_parts.append("")
        
        # بیت کوین
        btc = data.get('bitcoin', {})
        if btc.get('price_usd'):
            btc_price = int(btc['price_usd'])
            btc_irr = int(btc['price_usd'] * usd_to_irr)
            btc_change = btc.get('change_24h', 0)
            
            if btc_change > 0:
                change_icon = "🔺"
                change_text = f"+{btc_change:.2f}"
            elif btc_change < 0:
                change_icon = "🔻"
                change_text = f"{btc_change:.2f}"
            else:
                change_icon = "➖"
                change_text = "0.00"
            
            message_parts.append("🟠 بیت کوین (BTC):")
            message_parts.append(f"💵 ${btc_price:,}")
            message_parts.append(f"💰 {btc_irr:,} تومان")
            message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
            message_parts.append("")
        
        # اتریوم
        eth = data.get('ethereum', {})
        if eth.get('price_usd'):
            eth_price = int(eth['price_usd'])
            eth_irr = int(eth['price_usd'] * usd_to_irr)
            eth_change = eth.get('change_24h', 0)
            
            if eth_change > 0:
                change_icon = "🔺"
                change_text = f"+{eth_change:.2f}"
            elif eth_change < 0:
                change_icon = "🔻"
                change_text = f"{eth_change:.2f}"
            else:
                change_icon = "➖"
                change_text = "0.00"
            
            message_parts.append("🔵 اتریوم (ETH):")
            message_parts.append(f"💵 ${eth_price:,}")
            message_parts.append(f"💰 {eth_irr:,} تومان")
            message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
            message_parts.append("")
        
        # بیشترین صعود
        gainer = data.get('top_gainer', {})
        if gainer.get('symbol'):
            gainer_price = gainer.get('price_usd', 0)
            gainer_irr = int(gainer_price * usd_to_irr)
            gainer_change = gainer.get('change_24h', 0)
            
            message_parts.append("🚀 بیشترین صعود:")
            message_parts.append(f"🔥 {gainer['symbol']} ({gainer.get('name', 'N/A')})")
            message_parts.append(f"💵 ${gainer_price:.4f}")
            message_parts.append(f"💰 {gainer_irr:,} تومان")
            message_parts.append(f"🔺 +{gainer_change:.2f}%")
            message_parts.append("")
        
        # بیشترین نزول
        loser = data.get('top_loser', {})
        if loser.get('symbol'):
            loser_price = loser.get('price_usd', 0)
            loser_irr = int(loser_price * usd_to_irr)
            loser_change = loser.get('change_24h', 0)
            
            message_parts.append("📉 بیشترین نزول:")
            message_parts.append(f"💥 {loser['symbol']} ({loser.get('name', 'N/A')})")
            message_parts.append(f"💵 ${loser_price:.4f}")
            message_parts.append(f"💰 {loser_irr:,} تومان")
            message_parts.append(f"🔻 {loser_change:.2f}%")
            message_parts.append("")
        
        # خط جداکننده
        message_parts.append("━━━━━━━━━━━━━━━━━━")
        message_parts.append("")
        
        # تتر
        tether_price = data.get('tether_irr', 0)
        if tether_price > 0:
            tether_change = data.get('tether_change_24h', 0)
            
            if tether_change > 0:
                change_icon = "🔺"
                change_text = f"+{tether_change:.2f}"
            elif tether_change < 0:
                change_icon = "🔻"
                change_text = f"{tether_change:.2f}"
            else:
                change_icon = "➖"
                change_text = "0.00"
            
            message_parts.append("🟢 تتر (USDT):")
            message_parts.append(f"💰 {tether_price:,} تومان")
            if tether_change != 0:
                message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
            message_parts.append("")
        else:
            message_parts.append("🟢 تتر (USDT): ❌ ناموجود")
            message_parts.append("")
        
        # دلار
        usd_price = data.get('usd_irr', 0)
        if usd_price > 0:
            message_parts.append("💵 دلار آمریکا (USD):")
            message_parts.append(f"💰 {usd_price:,} تومان")
            message_parts.append("")
        else:
            message_parts.append("💵 دلار آمریکا (USD): ❌ ناموجود")
            message_parts.append("")
        
        # فوتر
        message_parts.append("🕐 آخرین بروزرسانی: همین الان")
        message_parts.append("📊 منبع: CoinGecko, تترلند, CodeBazan")
        
        return "\n".join(message_parts)
    
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
• 📰 آخرین اخبار کریپتو از منابع معتبر

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
                reply_markup=InlineKeyboardMarkup(keyboard)
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
    
    async def show_crypto_news(self, query):
        """نمایش آخرین اخبار کریپتو"""
        # نمایش پیام در حال بارگذاری
        loading_message = "⏳ در حال دریافت آخرین اخبار کریپتو...\n\nلطفاً چند ثانیه صبر کنید."
        await query.edit_message_text(loading_message)
        
        try:
            # دریافت اخبار
            news_list = await self.fetch_crypto_news()
            message = self.format_crypto_news_message(news_list)
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="crypto_news")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="public_crypto")]
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
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="crypto_news")],
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
            
            elif data == "crypto_news":
                await self.show_crypto_news(query)
            
            elif data == "public_ai":
                await self.show_ai_menu(query)
            
            elif data == "ai_news":
                await self.show_ai_news(query)
            
            else:
                await query.edit_message_text("❌ دستور نامعتبر")
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در پردازش: {str(e)}")
