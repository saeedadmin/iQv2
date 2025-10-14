#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TradingView Analysis Fetcher - بهبود یافته
دریافت آخرین تحلیل‌های TradingView برای ارزهای مختلف
"""

import aiohttp
import asyncio
import re
import html
import datetime
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

class TradingViewAnalysisFetcher:
    def __init__(self):
        self.base_url = "https://www.tradingview.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def normalize_to_usdt_pair(self, crypto_input: str) -> Optional[str]:
        """تبدیل ورودی کاربر به فرمت جفت ارز USDT"""
        if not crypto_input:
            return None
            
        # پاک کردن فاصله‌ها و تبدیل به lowercase
        clean_input = crypto_input.strip().lower().replace(' ', '')
        
        # اگر ورودی شامل usdt است، آن را استخراج کن
        if 'usdt' in clean_input:
            # مثال: ethusdt -> ETHUSDT
            if clean_input.endswith('usdt'):
                symbol = clean_input[:-4].upper()
                return f"{symbol}USDT"
            # مثال: eth/usdt -> ETHUSDT  
            elif '/usdt' in clean_input:
                symbol = clean_input.replace('/usdt', '').upper()
                return f"{symbol}USDT"
                
        # نقشه ارزها به USDT pairs
        crypto_map = {
            'bitcoin': 'BTCUSDT',
            'btc': 'BTCUSDT', 
            'بیت کوین': 'BTCUSDT',
            'بیتکوین': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'eth': 'ETHUSDT',
            'اتریوم': 'ETHUSDT',
            'اتر': 'ETHUSDT',
            'solana': 'SOLUSDT',
            'sol': 'SOLUSDT',
            'سولانا': 'SOLUSDT',
            'cardano': 'ADAUSDT',
            'ada': 'ADAUSDT',
            'کاردانو': 'ADAUSDT',
            'binance coin': 'BNBUSDT',
            'bnb': 'BNBUSDT',
            'بایننس': 'BNBUSDT',
            'xrp': 'XRPUSDT',
            'ripple': 'XRPUSDT',
            'ریپل': 'XRPUSDT',
            'dogecoin': 'DOGEUSDT',
            'doge': 'DOGEUSDT',
            'دوج': 'DOGEUSDT',
            'دوج کوین': 'DOGEUSDT',
            'chainlink': 'LINKUSDT',
            'link': 'LINKUSDT',
            'چین لینک': 'LINKUSDT',
            'litecoin': 'LTCUSDT',
            'ltc': 'LTCUSDT',
            'لایت کوین': 'LTCUSDT',
            'polkadot': 'DOTUSDT',
            'dot': 'DOTUSDT',
            'پولکادات': 'DOTUSDT',
            'avalanche': 'AVAXUSDT',
            'avax': 'AVAXUSDT',
            'اولانچ': 'AVAXUSDT',
            # ارزهای اضافی
            'matic': 'MATICUSDT',
            'polygon': 'MATICUSDT',
            'uni': 'UNIUSDT',
            'uniswap': 'UNIUSDT',
            'atom': 'ATOMUSDT',
            'cosmos': 'ATOMUSDT'
        }
        
        # بررسی نقشه ارزها
        if clean_input in crypto_map:
            return crypto_map[clean_input]
            
        # تلاش برای تشخیص خودکار فرمت
        # مثال: eth -> ETHUSDT
        if len(clean_input) <= 10 and clean_input.isalpha():
            potential_symbol = f"{clean_input.upper()}USDT"
            return potential_symbol
            
        return None
    
    async def scrape_live_analysis(self, symbol: str) -> Dict[str, Any]:
        """دریافت تحلیل زنده از TradingView"""
        try:
            # URL برای ایده‌های TradingView
            url = f"{self.base_url}/symbols/{symbol}/ideas/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # پارس کردن محتوا برای یافتن آخرین تحلیل
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # جستجو برای ایده‌های جدید - چندین selector امتحان کن
                        idea_selectors = [
                            'div[data-testid="idea-item"]',
                            '.tv-idea-card',
                            '.idea-card',
                            'article[data-testid="idea-card"]'
                        ]
                        
                        idea_elements = []
                        for selector in idea_selectors:
                            idea_elements = soup.select(selector)
                            if idea_elements:
                                break
                        
                        if idea_elements:
                            # گرفتن اولین (جدیدترین) ایده
                            first_idea = idea_elements[0]
                            
                            # استخراج اطلاعات
                            title_elem = first_idea.find('h3') or first_idea.find('a')
                            title = title_elem.get_text(strip=True) if title_elem else f"تحلیل {symbol}"
                            
                            # استخراج لینک
                            link_elem = first_idea.find('a', href=True)
                            analysis_url = f"{self.base_url}{link_elem['href']}" if link_elem else f"{self.base_url}/symbols/{symbol}/"
                            
                            # استخراج تصویر
                            img_elem = first_idea.find('img')
                            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
                            
                            return {
                                'success': True,
                                'title': title,
                                'analysis_url': analysis_url,
                                'image_url': image_url,
                                'symbol': symbol,
                                'description': f"🔥 آخرین تحلیل {symbol} از TradingView\n\n📊 {title}\n\n⏰ بروزرسانی: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                        
        except Exception as e:
            print(f"خطا در دریافت تحلیل زنده: {e}")
            
        return {'success': False}
    
    def get_backup_analysis(self, symbol: str) -> Dict[str, Any]:
        """دریافت تحلیل پشتیبان برای زمانی که API کار نکند"""
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        backup_data = {
            'BTCUSDT': {
                'title': 'Bitcoin Technical Analysis - آخرین روندها',
                'description': f'🚀 تحلیل بیت‌کوین - {current_time}\n\n📈 بررسی سطوح کلیدی و احتمال ادامه روند صعودی\n💡 سطوح حمایت و مقاومت مهم\n🎯 اهداف قیمتی کوتاه مدت',
                'symbol': 'BTCUSDT'
            },
            'ETHUSDT': {
                'title': 'Ethereum Price Action - نقاط کلیدی',
                'description': f'⚡ تحلیل اتریوم - {current_time}\n\n🔍 بررسی حرکت قیمت و الگوهای مهم\n📊 وضعیت فعلی و چشم‌انداز آینده\n💎 فرصت‌های معاملاتی',
                'symbol': 'ETHUSDT'
            },
            'SOLUSDT': {
                'title': 'Solana Outlook - چشم‌انداز صعودی',
                'description': f'🌟 نگاه به آینده سولانا - {current_time}\n\n🚀 momentum قوی و پتانسیل رشد\n📈 تحلیل فرصت‌های خرید\n🎯 اهداف قیمتی مهم',
                'symbol': 'SOLUSDT'
            }
        }
        
        if symbol in backup_data:
            data = backup_data[symbol].copy()
            data.update({
                'success': True,
                'analysis_url': f'{self.base_url}/symbols/{symbol}/',
                'image_url': None,
                'timestamp': current_time,
                'note': '📝 تحلیل از سیستم پشتیبان - لطفاً لحظاتی دیگر دوباره امتحان کنید'
            })
            return data
        else:
            return {
                'success': True,
                'title': f'{symbol} Technical Analysis',
                'description': f'📊 تحلیل تکنیکال {symbol} - {current_time}\n\n🔍 بررسی روند فعلی و سطوح کلیدی\n📈 الگوهای قیمتی مهم\n💡 راهنمای معاملاتی',
                'symbol': symbol,
                'analysis_url': f'{self.base_url}/symbols/{symbol}/',
                'image_url': None,
                'timestamp': current_time,
                'note': '📝 تحلیل عمومی - برای تحلیل تخصصی‌تر، نام ارز محبوب را وارد کنید'
            }
    
    async def fetch_latest_analysis(self, crypto_name: str) -> Dict[str, Any]:
        """دریافت آخرین تحلیل برای ارز مشخص شده"""
        try:
            # تبدیل نام ارز به فرمت USDT
            normalized_symbol = self.normalize_to_usdt_pair(crypto_name)
            if not normalized_symbol:
                return {
                    'success': False,
                    'error': f'❌ ارز "{crypto_name}" پشتیبانی نمی‌شود\n\n✅ فرمت‌های صحیح:\n• BTC، ETH، SOL\n• ETHUSDT، BTCUSDT\n• ETH/USDT، BTC/USDT'
                }
            
            # تلاش برای دریافت تحلیل واقعی از TradingView
            real_analysis = await self.scrape_live_analysis(normalized_symbol)
            if real_analysis and real_analysis.get('success'):
                return real_analysis
            
            # در صورت عدم موفقیت، استفاده از داده‌های پشتیبان
            backup_data = self.get_backup_analysis(normalized_symbol)
            return backup_data
                
        except Exception as e:
            return {
                'success': False,
                'error': f"❌ خطا در دریافت تحلیل: {str(e)}\n\nلطفاً دوباره امتحان کنید یا نام ارز دیگری وارد کنید."
            }
    
    def format_analysis_message(self, analysis_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام تحلیل برای ارسال در تلگرام"""
        if not analysis_data.get('success'):
            return analysis_data.get('error', 'خطا در دریافت تحلیل')
        
        title = analysis_data.get('title', '')
        description = analysis_data.get('description', '')
        symbol = analysis_data.get('symbol', '')
        analysis_url = analysis_data.get('analysis_url', '')
        note = analysis_data.get('note', '')
        
        message = f"📊 **تحلیل {symbol}**\n\n"
        message += f"📰 **{title}**\n\n"
        message += f"{description}\n\n"
        
        if note:
            message += f"{note}\n\n"
        
        if analysis_url:
            message += f"🔗 [مشاهده تحلیل کامل]({analysis_url})\n\n"
        
        message += "💡 *این تحلیل جنبه آموزشی دارد و نباید به عنوان توصیه سرمایه‌گذاری در نظر گرفته شود.*"
        
        return message
