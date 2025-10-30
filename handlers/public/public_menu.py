#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Public Menu Manager
مدیریت منوی عمومی و دریافت اخبار
"""

import logging
from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class PublicMenuManager:
    """مدیریت منوی عمومی و دریافت اخبار"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.logger = logger
    
    async def fetch_crypto_prices(self):
        """دریافت قیمت‌های ارز دیجیتال"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin,ethereum,binancecoin,ripple,cardano,solana,polkadot,dogecoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            
            async with ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            self.logger.error(f"خطا در دریافت قیمت‌ها: {e}")
            return None
    
    def format_crypto_message(self, data):
        """فرمت پیام قیمت‌های کریپتو"""
        if not data:
            return "❌ خطا در دریافت قیمت‌ها"
        
        message = "📊 **قیمت‌های لحظه‌ای ارزهای دیجیتال**\n\n"
        
        crypto_names = {
            "bitcoin": "🪙 Bitcoin (BTC)",
            "ethereum": "⛓️ Ethereum (ETH)",
            "binancecoin": "🔶 BNB",
            "ripple": "🔷 Ripple (XRP)",
            "cardano": "🔵 Cardano (ADA)",
            "solana": "🟣 Solana (SOL)",
            "polkadot": "🔴 Polkadot (DOT)",
            "dogecoin": "🐕 Dogecoin (DOGE)"
        }
        
        for coin_id, coin_data in data.items():
            name = crypto_names.get(coin_id, coin_id.title())
            price = coin_data.get('usd', 0)
            change_24h = coin_data.get('usd_24h_change', 0)
            
            change_emoji = "📈" if change_24h > 0 else "📉"
            change_text = f"+{change_24h:.2f}%" if change_24h > 0 else f"{change_24h:.2f}%"
            
            message += f"{name}\n┏ 💵 Price: ${price:,.2f}\n┗ {change_emoji} 24h: {change_text}\n\n"
        
        return message
    
    async def fetch_crypto_news(self):
        """دریافت اخبار کریپتو"""
        # TODO: Implement real API - currently returns mock data
        return [
            {"title": "اخبار کریپتو 1", "url": "#"},
            {"title": "اخبار کریپتو 2", "url": "#"}
        ]
    
    def format_crypto_news_message(self, news_list):
        """فرمت پیام اخبار کریپتو"""
        if not news_list:
            return "❌ اخباری یافت نشد"
        
        message = "📰 **آخرین اخبار کریپتو**\n\n"
        for i, news in enumerate(news_list[:5], 1):
            message += f"{i}. {news.get('title', 'N/A')}\n"
        return message
    
    async def fetch_general_news(self):
        """دریافت اخبار عمومی"""
        # TODO: Implement real API - currently returns mock data
        return [
            {"title": "اخبار عمومی 1", "url": "#"},
            {"title": "اخبار عمومی 2", "url": "#"}
        ]
    
    def format_general_news_message(self, news_list):
        """فرمت پیام اخبار عمومی"""
        if not news_list:
            return "❌ اخباری یافت نشد"
        
        message = "📺 **آخرین اخبار روز**\n\n"
        for i, news in enumerate(news_list[:10], 1):
            message += f"{i}. {news.get('title', 'N/A')}\n"
        return message
    
    async def fetch_ai_news(self):
        """دریافت اخبار هوش مصنوعی"""
        # TODO: Implement real API - currently returns mock data
        return [
            {"title": "اخبار AI 1", "url": "#"},
            {"title": "اخبار AI 2", "url": "#"}
        ]
    
    def format_ai_news_message(self, news_list):
        """فرمت پیام اخبار هوش مصنوعی"""
        if not news_list:
            return "❌ اخباری یافت نشد"
        
        message = "🤖 **آخرین اخبار هوش مصنوعی**\n\n"
        for i, news in enumerate(news_list[:10], 1):
            message += f"{i}. {news.get('title', 'N/A')}\n"
        return message
    
    async def handle_public_callback(self, update, context):
        """مدیریت callback queries بخش عمومی"""
        query = update.callback_query
        await query.answer()
        # TODO: Implement callback handling if needed
        pass
