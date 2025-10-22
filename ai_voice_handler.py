#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت تبدیل صدا به متن و متن به صدا با Self-Hosted API
نویسنده: MiniMax Agent

قابلیت‌ها:
- Text to Speech (TTS): تبدیل متن به صدا با Coqui TTS
- Speech to Text (STT): تبدیل صدا به متن با Whisper
- Rate Limiting: محدودیت 10 درخواست در روز برای کاربران عادی
- Character Limiting: محدودیت 200 کاراکتر برای کاربران عادی
- پشتیبانی کامل از زبان فارسی
"""

import logging
import os
import datetime
import tempfile
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AIVoiceHandler:
    """مدیریت تبدیل صدا به متن و متن به صدا"""
    
    def __init__(self, api_url: str = None, db_manager = None):
        """مقداردهی handler صدا"""
        self.api_url = api_url or os.getenv('VOICE_API_URL', 'https://saeedm777-stt.hf.space')
        self.db = db_manager
        
        # تنظیمات محدودیت
        self.max_requests_per_day = 10  # حداکثر درخواست روزانه برای کاربران عادی
        self.max_characters = 200  # حداکثر تعداد کاراکتر برای کاربران عادی (افزایش یافته)
        
        # تنظیمات timeout برای درخواست‌ها
        self.request_timeout = 60  # 60 ثانیه برای درخواست‌های طولانی
        
        # ذخیره استفاده روزانه کاربران
        self.user_daily_usage = {}  # {user_id: {'date': date, 'count': int}}
        
        logger.info(f"✅ AIVoiceHandler با Self-Hosted API مقداردهی شد: {self.api_url}")
    
    def _check_daily_limit(self, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """
        بررسی محدودیت روزانه کاربر
        
        Args:
            user_id: شناسه کاربر
            is_admin: آیا کاربر ادمین است
            
        Returns:
            Dictionary با کلیدهای:
            - allowed: Boolean
            - remaining: تعداد باقیمانده
            - error_message: پیام خطا (در صورت وجود)
        """
        # ادمین محدودیت ندارد
        if is_admin:
            return {'allowed': True, 'remaining': -1, 'error_message': None}
        
        today = datetime.date.today()
        
        # بررسی آیا کاربر امروز درخواست داده
        if user_id not in self.user_daily_usage:
            self.user_daily_usage[user_id] = {'date': today, 'count': 0}
        else:
            # اگر تاریخ تغییر کرده، ریست کن
            if self.user_daily_usage[user_id]['date'] != today:
                self.user_daily_usage[user_id] = {'date': today, 'count': 0}
        
        current_count = self.user_daily_usage[user_id]['count']
        
        if current_count >= self.max_requests_per_day:
            return {
                'allowed': False,
                'remaining': 0,
                'error_message': f"❌ محدودیت روزانه\n\nشما امروز {self.max_requests_per_day} درخواست داده‌اید.\n⏰ لطفاً فردا دوباره تلاش کنید."
            }
        
        return {
            'allowed': True,
            'remaining': self.max_requests_per_day - current_count - 1,
            'error_message': None
        }
    
    def _increment_usage(self, user_id: int, is_admin: bool = False):
        """افزایش شمارنده استفاده روزانه"""
        if is_admin:
            return  # ادمین محدودیت ندارد
        
        today = datetime.date.today()
        if user_id not in self.user_daily_usage or self.user_daily_usage[user_id]['date'] != today:
            self.user_daily_usage[user_id] = {'date': today, 'count': 1}
        else:
            self.user_daily_usage[user_id]['count'] += 1
    
    def text_to_speech(self, text: str, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """
        تبدیل متن به صدا
        
        Args:
            text: متن ورودی
            user_id: شناسه کاربر
            is_admin: آیا کاربر ادمین است
            
        Returns:
            Dictionary با کلیدهای:
            - success: Boolean
            - audio_file: مسیر فایل صوتی (در صورت موفقیت)
            - error: پیام خطا (در صورت وجود)
            - remaining: تعداد درخواست باقیمانده
        """
        try:
            # بررسی محدودیت روزانه
            limit_check = self._check_daily_limit(user_id, is_admin)
            if not limit_check['allowed']:
                return {
                    'success': False,
                    'audio_file': None,
                    'error': limit_check['error_message'],
                    'remaining': 0
                }
            
            # بررسی محدودیت تعداد کاراکتر (فقط برای غیر ادمین)
            if not is_admin and len(text) > self.max_characters:
                return {
                    'success': False,
                    'audio_file': None,
                    'error': f"❌ تعداد کاراکترها بیش از حد مجاز\n\nحداکثر: {self.max_characters} کاراکتر\nشما: {len(text)} کاراکتر\n\n💡 لطفاً متن کوتاه‌تری ارسال کنید.",
                    'remaining': limit_check['remaining']
                }
            
            # تبدیل متن به صدا با Self-Hosted API
            logger.info(f"🎤 تبدیل متن به صدا برای کاربر {user_id} ({len(text)} کاراکتر)")
            
            # ارسال درخواست به API
            response = requests.post(
                f"{self.api_url}/tts",
                params={"text": text},  # استفاده از query parameter
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            # ذخیره فایل صوتی در پوشه موقت
            temp_dir = tempfile.gettempdir()
            audio_filename = f"tts_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            audio_path = os.path.join(temp_dir, audio_filename)
            
            # نوشتن بایت‌های صوتی در فایل
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            # افزایش شمارنده استفاده
            self._increment_usage(user_id, is_admin)
            
            logger.info(f"✅ تبدیل متن به صدا موفق: {audio_path}")
            
            return {
                'success': True,
                'audio_file': audio_path,
                'error': None,
                'remaining': limit_check['remaining']
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در تبدیل متن به صدا: {e}", exc_info=True)
            return {
                'success': False,
                'audio_file': None,
                'error': f"❌ خطا در تبدیل متن به صدا\n\n{str(e)}",
                'remaining': limit_check.get('remaining', 0) if 'limit_check' in locals() else 0
            }
    
    def speech_to_text(self, audio_file_path: str, user_id: int, is_admin: bool = False) -> Dict[str, Any]:
        """
        تبدیل صدا به متن
        
        Args:
            audio_file_path: مسیر فایل صوتی
            user_id: شناسه کاربر
            is_admin: آیا کاربر ادمین است
            
        Returns:
            Dictionary با کلیدهای:
            - success: Boolean
            - text: متن تبدیل شده (در صورت موفقیت)
            - error: پیام خطا (در صورت وجود)
            - remaining: تعداد درخواست باقیمانده
        """
        try:
            # بررسی محدودیت روزانه
            limit_check = self._check_daily_limit(user_id, is_admin)
            if not limit_check['allowed']:
                return {
                    'success': False,
                    'text': None,
                    'error': limit_check['error_message'],
                    'remaining': 0
                }
            
            # بررسی وجود فایل
            if not os.path.exists(audio_file_path):
                return {
                    'success': False,
                    'text': None,
                    'error': "❌ فایل صوتی یافت نشد",
                    'remaining': limit_check['remaining']
                }
            
            # تبدیل صدا به متن با Self-Hosted API
            logger.info(f"📝 تبدیل صدا به متن برای کاربر {user_id}")
            
            # ارسال درخواست به API
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': audio_file}
                response = requests.post(
                    f"{self.api_url}/stt",
                    files=files,
                    timeout=self.request_timeout
                )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            # استخراج متن از پاسخ JSON
            result = response.json()
            text = result.get('text', '')
            
            if not text:
                raise Exception("متنی دریافت نشد")
            
            # افزایش شمارنده استفاده
            self._increment_usage(user_id, is_admin)
            
            logger.info(f"✅ تبدیل صدا به متن موفق: {len(text)} کاراکتر")
            
            return {
                'success': True,
                'text': text,
                'error': None,
                'remaining': limit_check['remaining']
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در تبدیل صدا به متن: {e}", exc_info=True)
            return {
                'success': False,
                'text': None,
                'error': f"❌ خطا در تبدیل صدا به متن\n\n{str(e)}",
                'remaining': limit_check.get('remaining', 0) if 'limit_check' in locals() else 0
            }
    
    def get_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """
        دریافت آمار استفاده روزانه کاربر
        
        Args:
            user_id: شناسه کاربر
            
        Returns:
            Dictionary با آمار استفاده
        """
        today = datetime.date.today()
        
        if user_id not in self.user_daily_usage or self.user_daily_usage[user_id]['date'] != today:
            return {
                'today': 0,
                'remaining': self.max_requests_per_day,
                'limit': self.max_requests_per_day
            }
        
        used = self.user_daily_usage[user_id]['count']
        return {
            'today': used,
            'remaining': max(0, self.max_requests_per_day - used),
            'limit': self.max_requests_per_day
        }
