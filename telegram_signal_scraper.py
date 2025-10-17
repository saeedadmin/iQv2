#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Channel Scraper Module
استخراج سیگنال‌های ترید از کانال‌های تلگرام
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from apify_client import ApifyClient

class TelegramSignalScraper:
    """کلاس برای استخراج سیگنال‌های ترید از کانال‌های تلگرام"""
    
    def __init__(self, api_key: str = None):
        """
        راه‌اندازی scraper
        Args:
            api_key: کلید API سرویس Apify
        """
        self.api_key = api_key or os.getenv('APIFY_API_KEY', 'apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc')
        self.client = ApifyClient(self.api_key)
        
        # کانال‌های هدف
        self.channels = [
            "Shervin_Trading",  # کانال شروین تریدینگ
            # "uniopn",  # کانال دوم (نیاز به login دارد)
        ]
        
        # کلیدواژه‌های تشخیص سیگنال
        self.signal_keywords = [
            'سیگنال', 'ارز', 'لانگ', 'شورت', 'اهداف', '🚨',
            'signal', 'long', 'short', 'entry', 'target', 'stop'
        ]
    
    async def fetch_latest_signals(self, days: int = 3, max_signals: int = 2) -> List[Dict]:
        """
        دریافت آخرین سیگنال‌های ترید - بهبود یافته
        
        Args:
            days: تعداد روزهای گذشته برای جستجو
            max_signals: حداکثر تعداد سیگنال (پیش‌فرض: 2)
            
        Returns:
            لیست سیگنال‌های استخراج شده بدون تکرار
        """
        all_signals = []
        
        for channel in self.channels:
            try:
                channel_signals = await self._scrape_channel(channel, days)
                all_signals.extend(channel_signals)
            except Exception as e:
                print(f"❌ خطا در دریافت سیگنال از کانال {channel}: {e}")
                continue
        
        # حذف سیگنال‌های تکراری بر اساس coin_pair و تاریخ
        unique_signals = self._remove_duplicates(all_signals)
        
        # مرتب‌سازی براساس تاریخ (جدیدترین اول)
        unique_signals.sort(key=lambda x: x.get('fulldate', '1900-01-01'), reverse=True)
        
        # برگرداندن حداکثر تعداد مشخص شده
        return unique_signals[:max_signals]
    
    def _remove_duplicates(self, signals: List[Dict]) -> List[Dict]:
        """
        حذف سیگنال‌های تکراری
        
        Args:
            signals: لیست کل سیگنال‌ها
            
        Returns:
            لیست سیگنال‌های یکتا
        """
        seen = set()
        unique_signals = []
        
        for signal in signals:
            # ایجاد کلید یکتا برای هر سیگنال
            signal_key = (
                signal.get('coin_pair', 'UNKNOWN'),
                signal.get('signal_type', 'UNKNOWN'),
                signal.get('date', 'N/A')
            )
            
            if signal_key not in seen:
                seen.add(signal_key)
                unique_signals.append(signal)
        
        return unique_signals
    
    async def _scrape_channel(self, channel: str, days: int) -> List[Dict]:
        """
        استخراج سیگنال‌ها از یک کانال مشخص
        
        Args:
            channel: نام کانال
            days: تعداد روزهای گذشته
            
        Returns:
            لیست سیگنال‌های کانال
        """
        try:
            print(f"🔍 استخراج سیگنال‌ها از @{channel}...")
            
            # تنظیم ورودی برای Apify actor
            run_input = {
                "collectMessages": True,
                "profiles": [channel],
                "scrapeLastNDays": days
            }
            
            # اجرای actor
            run = self.client.actor("tri_angle/telegram-scraper").call(run_input=run_input)
            
            # دریافت نتایج
            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)
            
            # استخراج سیگنال‌ها
            signals = self._extract_signals_from_results(results, channel)
            
            print(f"✅ {len(signals)} سیگنال از @{channel} دریافت شد")
            return signals
            
        except Exception as e:
            print(f"❌ خطا در استخراج از @{channel}: {e}")
            return []
    
    def _extract_signals_from_results(self, results: List[Dict], channel: str) -> List[Dict]:
        """
        استخراج سیگنال‌ها از نتایج خام
        
        Args:
            results: نتایج خام از Apify
            channel: نام کانال
            
        Returns:
            لیست سیگنال‌های پردازش شده
        """
        signals = []
        
        # مرتب‌سازی براساس تاریخ
        results_sorted = sorted(
            results, 
            key=lambda x: x['message']['fulldate'] if x.get('message') and x['message'].get('fulldate') else '1900-01-01', 
            reverse=True
        )
        
        for result in results_sorted:
            if not result.get('message') or not result['message'].get('description'):
                continue
                
            message = result['message']
            description = message['description']
            
            # بررسی اینکه آیا پیام سیگنال است
            if self._is_trading_signal(description):
                signal = {
                    'channel': f"@{channel}",
                    'date': message.get('date', 'N/A'),
                    'fulldate': message.get('fulldate', 'N/A'),
                    'views': message.get('views', 0),
                    'text': description,
                    'link': message.get('link', ''),
                    'has_image': bool(message.get('image')),
                    'has_video': bool(message.get('video')),
                    'signal_type': self._detect_signal_type(description),
                    'coin_pair': self._extract_coin_pair(description)
                }
                signals.append(signal)
        
        return signals
    
    def _is_trading_signal(self, text: str) -> bool:
        """
        تشخیص اینکه آیا متن یک سیگنال ترید است
        
        Args:
            text: متن پیام
            
        Returns:
            True اگر سیگنال باشد
        """
        text_lower = text.lower()
        
        # بررسی وجود کلیدواژه‌های سیگنال
        for keyword in self.signal_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # بررسی الگوهای مشخص سیگنال
        signal_patterns = [
            'entry', 'target', 'stop', 'leverage',
            'ورود', 'هدف', 'استاپ', 'لوریج'
        ]
        
        found_patterns = 0
        for pattern in signal_patterns:
            if pattern.lower() in text_lower:
                found_patterns += 1
        
        # اگر حداقل 2 الگو پیدا شد، احتمالاً سیگنال است
        return found_patterns >= 2
    
    def _detect_signal_type(self, text: str) -> str:
        """
        تشخیص نوع سیگنال (Long/Short)
        
        Args:
            text: متن سیگنال
            
        Returns:
            نوع سیگنال
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['لانگ', 'long', '📈']):
            return 'LONG'
        elif any(word in text_lower for word in ['شورت', 'short', '📉']):
            return 'SHORT'
        else:
            return 'UNKNOWN'
    
    def _extract_coin_pair(self, text: str) -> str:
        """
        استخراج جفت ارز از متن سیگنال
        
        Args:
            text: متن سیگنال
            
        Returns:
            جفت ارز (مثل BTC/USDT)
        """
        import re
        
        # الگوهای مختلف جفت ارز
        patterns = [
            r'([A-Z]{2,10})\s*/\s*USDT',
            r'([A-Z]{2,10})\s*/\s*USD',
            r'([A-Z]{2,10})\s*/\s*BTC',
            r'ارز\s*:\s*([A-Z]{2,10})',
            r'💎\s*ارز\s*:\s*([A-Z]{2,10})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                coin = match.group(1).upper()
                if 'USDT' in text.upper():
                    return f"{coin}/USDT"
                elif 'USD' in text.upper():
                    return f"{coin}/USD"
                elif 'BTC' in text.upper():
                    return f"{coin}/BTC"
                return coin
        
        return 'UNKNOWN'
    
    def _clean_signal_text(self, text: str) -> str:
        """
        تمیز کردن متن سیگنال از کلمات اضافی و تکراری
        
        Args:
            text: متن خام سیگنال
            
        Returns:
            متن تمیز شده
        """
        import re
        
        # حذف متن‌های تبلیغاتی و اضافی
        unwanted_phrases = [
            r'🚨\s*سیگنال اختصاصی برای اعضای کانال\s*🚨',
            r'🔥\s*سیگنال جدید از.*?🔥',
            r'⚠️\s*مدیریت سرمایه و رعایت حد ضرر.*?است[\.]*',
            r'نوش جان.*?$',
            r'💵.*?تاچ.*?رفقا.*?$',
            r'💵.*?تارگت.*?تاچ.*?$',
            r'ضروری است',
            r'اولین قدم برای موفقیت است',
            r'ضروری است\.+',
            r'\.{3,}.*$'  # حذف سه نقطه و متن بعدش
        ]
        
        cleaned_text = text
        for phrase in unwanted_phrases:
            cleaned_text = re.sub(phrase, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # حذف خطوط خالی اضافی
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)
        
        # حذف فضاهای اضافی
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # حذف جفت ارز اضافی اگر قبلاً در header ذکر شده
        coin_patterns = [
            r'💎\s*ارز\s*:\s*[A-Z]+\s*/\s*USDT',
            r'💎\s*ارز\s*:\s*[A-Z]+\s*/\s*USD',
            r'💎\s*ارز\s*:\s*[A-Z]+\s*/\s*BTC'
        ]
        
        for pattern in coin_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text.strip()

    def format_signal_for_display(self, signal: Dict) -> str:
        """
        فرمت کردن سیگنال برای نمایش - بهبود یافته و تمیز
        
        Args:
            signal: دیکشنری سیگنال
            
        Returns:
            متن فرمت شده و تمیز
        """
        # تمیز کردن متن سیگنال
        raw_text = signal['text']
        cleaned_text = self._clean_signal_text(raw_text)
        
        # اگر متن خیلی طولانی باشد، کوتاه کن
        if len(cleaned_text) > 350:
            # پیدا کردن آخرین فاصله قبل از 350 کاراکتر
            cut_pos = cleaned_text.rfind(' ', 0, 350)
            if cut_pos > 250:  # اگر جای مناسبی پیدا شد
                cleaned_text = cleaned_text[:cut_pos] + '...'
            else:
                cleaned_text = cleaned_text[:350] + '...'
        
        # ساخت پیام فرمت شده
        formatted = f"📅 **تاریخ:** {signal['date']}\n"
        formatted += f"💰 **ارز:** {signal['coin_pair']}\n"
        formatted += f"📊 **نوع:** {signal['signal_type']}\n"
        formatted += f"👀 **بازدید:** {signal['views']:,}\n\n"
        formatted += f"💬 **سیگنال:**\n{cleaned_text}"
        
        return formatted

# تابع helper برای ربات
async def get_latest_crypto_signals(days: int = 3, max_signals: int = 2) -> List[str]:
    """
    دریافت آخرین سیگنال‌های کریپتو برای ربات - بهبود یافته
    
    Args:
        days: تعداد روزهای گذشته
        max_signals: حداکثر تعداد سیگنال (پیش‌فرض: 2)
        
    Returns:
        لیست سیگنال‌های فرمت شده و تمیز برای نمایش
    """
    try:
        scraper = TelegramSignalScraper()
        signals = await scraper.fetch_latest_signals(days, max_signals)
        
        if not signals:
            return ["❌ هیچ سیگنال جدیدی یافت نشد"]
        
        formatted_signals = []
        for signal in signals:
            formatted = scraper.format_signal_for_display(signal)
            formatted_signals.append(formatted)
        
        return formatted_signals
        
    except Exception as e:
        print(f"❌ خطا در دریافت سیگنال‌ها: {e}")
        return [f"❌ خطا در دریافت سیگنال‌ها: {str(e)}"]

# تست اسکریپت
if __name__ == "__main__":
    async def test_scraper():
        print("🧪 تست Telegram Signal Scraper...")
        signals = await get_latest_crypto_signals(days=2, max_signals=3)
        
        for i, signal in enumerate(signals, 1):
            print(f"\n{'='*60}")
            print(f"Signal {i}:")
            print(signal)
    
    asyncio.run(test_scraper())