#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت چت با هوش مصنوعی (نسخه پیشرفته)
نویسنده: MiniMax Agent

قابلیت‌ها:
- حافظه مکالمه (Chat History)
- Rate Limiting (محدودیت تعداد پیام)
- فرمت کد با syntax highlighting
- امنیت و sanitization
- پشتیبانی از Google Gemini API
"""

import logging
import requests
import html
import re
import datetime
import time
import asyncio
from typing import Optional, Dict, Any, List
import os

logger = logging.getLogger(__name__)

class GeminiChatHandler:
    """مدیریت چت با Google Gemini API با حافظه مکالمه"""
    
    def __init__(self, api_key: str = None, db_manager = None):
        """مقداردهی هندلر چت"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyA8HKbAXWjvh_cKQ8ynbyXztw6zIczelGk')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-2.0-flash-exp"
        self.db = db_manager
        
        # تنظیمات محدودیت
        self.max_message_length = 4000  # حداکثر طول پیام کاربر
        self.timeout = 30  # تایم‌اوت درخواست
        self.max_history_messages = 50  # حداکثر تعداد پیام‌های تاریخچه
        
        # Rate Limiting
        self.rate_limit_messages = 10  # تعداد پیام مجاز
        self.rate_limit_seconds = 60  # در چند ثانیه
        self.user_message_times = {}  # ذخیره زمان پیام‌های کاربران
        
        # Retry Settings
        self.max_retries = 3  # حداکثر تعداد تلاش مجدد
        self.retry_delay_base = 2  # تأخیر پایه برای retry (ثانیه)
        
        # ثبت پیام فقط در دیباگ
        logger.debug("✅ GeminiChatHandler با حافظه مکالمه مقداردهی شد")
    
    def check_rate_limit(self, user_id: int) -> Dict[str, Any]:
        """بررسی محدودیت تعداد پیام"""
        current_time = datetime.datetime.now()
        
        # اگر کاربر جدید است
        if user_id not in self.user_message_times:
            self.user_message_times[user_id] = []
        
        # حذف پیام‌های قدیمی (بیش از rate_limit_seconds)
        cutoff_time = current_time - datetime.timedelta(seconds=self.rate_limit_seconds)
        self.user_message_times[user_id] = [
            t for t in self.user_message_times[user_id] 
            if t > cutoff_time
        ]
        
        # بررسی تعداد پیام‌ها
        message_count = len(self.user_message_times[user_id])
        
        if message_count >= self.rate_limit_messages:
            # محاسبه زمان باقی‌مانده
            oldest_message_time = min(self.user_message_times[user_id])
            wait_time = (oldest_message_time + datetime.timedelta(seconds=self.rate_limit_seconds)) - current_time
            wait_seconds = int(wait_time.total_seconds())
            
            return {
                'allowed': False,
                'wait_time': wait_seconds,
                'message_count': message_count
            }
        
        # ثبت پیام جدید
        self.user_message_times[user_id].append(current_time)
        
        return {
            'allowed': True,
            'remaining': self.rate_limit_messages - message_count - 1
        }
    
    def sanitize_input(self, text: str) -> str:
        """پاکسازی ورودی از کاراکترهای خطرناک"""
        # حذف کاراکترهای کنترلی خطرناک
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        
        # محدود کردن طول
        if len(text) > self.max_message_length:
            text = text[:self.max_message_length]
            logger.warning(f"⚠️ پیام به {self.max_message_length} کاراکتر محدود شد")
        
        return text.strip()
    
    def _make_api_request(self, payload: Dict[str, Any], attempt: int = 1) -> Dict[str, Any]:
        """
        ارسال درخواست به API با retry logic
        
        Args:
            payload: داده‌های ارسالی
            attempt: شماره تلاش فعلی
            
        Returns:
            Dictionary حاوی نتیجه درخواست
        """
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # بررسی status code
            if response.status_code == 200:
                return {
                    'success': True,
                    'response': response,
                    'status_code': 200
                }
            
            # خطاهای 5xx (Server Errors) - قابل retry
            elif response.status_code in [500, 503, 504]:
                error_detail = response.text
                logger.warning(
                    f"⚠️ خطای سرور {response.status_code} (تلاش {attempt}/{self.max_retries}): {error_detail}"
                )
                
                # اگر هنوز تلاش باقی مانده، retry کن
                if attempt < self.max_retries:
                    # Exponential backoff: 2, 4, 8 ثانیه
                    delay = self.retry_delay_base ** attempt
                    logger.info(f"⏳ صبر {delay} ثانیه قبل از تلاش مجدد...")
                    time.sleep(delay)
                    
                    # تلاش مجدد
                    return self._make_api_request(payload, attempt + 1)
                else:
                    # تمام تلاش‌ها شکست خورد
                    return {
                        'success': False,
                        'error_type': 'server_overload',
                        'status_code': response.status_code,
                        'detail': error_detail
                    }
            
            # خطاهای 4xx (Client Errors) - غیرقابل retry
            else:
                error_detail = response.text
                logger.error(f"❌ خطای API {response.status_code}: {error_detail}")
                return {
                    'success': False,
                    'error_type': 'client_error',
                    'status_code': response.status_code,
                    'detail': error_detail
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout در تلاش {attempt}/{self.max_retries}")
            
            if attempt < self.max_retries:
                delay = self.retry_delay_base ** attempt
                logger.info(f"⏳ صبر {delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(delay)
                return self._make_api_request(payload, attempt + 1)
            else:
                return {
                    'success': False,
                    'error_type': 'timeout',
                    'status_code': None,
                    'detail': 'زمان درخواست به پایان رسید'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطا در ارتباط با API (تلاش {attempt}): {e}")
            
            if attempt < self.max_retries:
                delay = self.retry_delay_base ** attempt
                logger.info(f"⏳ صبر {delay} ثانیه قبل از تلاش مجدد...")
                time.sleep(delay)
                return self._make_api_request(payload, attempt + 1)
            else:
                return {
                    'success': False,
                    'error_type': 'network_error',
                    'status_code': None,
                    'detail': str(e)
                }
    
    def send_message_with_history(self, user_id: int, user_message: str) -> Dict[str, Any]:
        """
        ارسال پیام به Google Gemini با استفاده از تاریخچه مکالمه
        
        Args:
            user_id: شناسه کاربر
            user_message: پیام کاربر
            
        Returns:
            Dictionary با کلیدهای:
            - success: Boolean
            - response: متن پاسخ AI
            - tokens_used: تعداد توکن‌های استفاده شده
            - error: پیام خطا (در صورت وجود)
            - error_type: نوع خطا (در صورت وجود)
        """
        try:
            # بررسی Rate Limit
            rate_check = self.check_rate_limit(user_id)
            if not rate_check['allowed']:
                wait_time = rate_check['wait_time']
                return {
                    'success': False,
                    'error': f'rate_limit:{wait_time}',
                    'error_type': 'rate_limit',
                    'response': None,
                    'tokens_used': 0
                }
            
            # پاکسازی ورودی
            user_message = self.sanitize_input(user_message)
            
            if not user_message:
                return {
                    'success': False,
                    'error': 'پیام خالی است',
                    'error_type': 'empty_message',
                    'response': None,
                    'tokens_used': 0
                }
            
            # دریافت تاریخچه چت از دیتابیس
            chat_history = []
            if self.db:
                chat_history = self.db.get_chat_history(user_id, limit=self.max_history_messages)
                logger.info(f"📚 بارگذاری {len(chat_history)} پیام از تاریخچه کاربر {user_id}")
            
            # ساخت contents با تاریخچه
            contents = []
            
            # اضافه کردن تاریخچه
            for msg in chat_history:
                contents.append({
                    "role": msg['role'],
                    "parts": [{"text": msg['message_text']}]
                })
            
            # اضافه کردن پیام جدید کاربر
            contents.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            
            # ساخت payload
            payload = {
                "contents": contents
            }
            
            logger.info(f"🚀 ارسال درخواست به Gemini (تعداد پیام‌ها: {len(contents)})")
            
            # ارسال درخواست با retry logic
            api_result = self._make_api_request(payload)
            
            if not api_result['success']:
                # خطا رخ داده - تشخیص نوع خطا
                error_type = api_result.get('error_type')
                status_code = api_result.get('status_code')
                
                if error_type == 'server_overload':
                    # سرور overload است
                    return {
                        'success': False,
                        'error': f'server_overload:{status_code}',
                        'error_type': 'server_overload',
                        'response': None,
                        'tokens_used': 0
                    }
                elif error_type == 'timeout':
                    return {
                        'success': False,
                        'error': 'timeout',
                        'error_type': 'timeout',
                        'response': None,
                        'tokens_used': 0
                    }
                elif error_type == 'network_error':
                    return {
                        'success': False,
                        'error': 'network_error',
                        'error_type': 'network_error',
                        'response': None,
                        'tokens_used': 0
                    }
                else:
                    # خطای کلاینت (4xx)
                    return {
                        'success': False,
                        'error': f'client_error:{status_code}',
                        'error_type': 'client_error',
                        'response': None,
                        'tokens_used': 0
                    }
            
            # موفقیت - Parse کردن پاسخ
            response = api_result['response']
            result = response.json()
            
            # استخراج متن پاسخ
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                tokens_used = result.get('usageMetadata', {}).get('totalTokenCount', 0)
                
                logger.info(f"✅ پاسخ موفق از Gemini (توکن‌ها: {tokens_used})")
                
                # ذخیره پیام کاربر و پاسخ AI در تاریخچه
                if self.db:
                    self.db.add_chat_message(user_id, 'user', user_message)
                    self.db.add_chat_message(user_id, 'model', ai_text)
                
                return {
                    'success': True,
                    'response': ai_text,
                    'tokens_used': tokens_used,
                    'error': None,
                    'error_type': None
                }
            else:
                logger.error(f"❌ پاسخ نامعتبر از API: {result}")
                return {
                    'success': False,
                    'error': 'invalid_response',
                    'error_type': 'invalid_response',
                    'response': None,
                    'tokens_used': 0
                }
                
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره در GeminiChat: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'unexpected_error',
                'error_type': 'unexpected_error',
                'response': None,
                'tokens_used': 0
            }
    
    def format_code_blocks(self, text: str) -> str:
        """
        تشخیص و فرمت کردن کدهای درون متن با استفاده از تگ‌های تلگرام
        
        Args:
            text: متن حاوی کد
            
        Returns:
            متن فرمت شده با تگ‌های HTML
        """
        # الگوی Markdown code blocks (```language\ncode\n```)
        code_block_pattern = r'```([a-z]*)?\n([\s\S]*?)```'
        
        def replace_code_block(match):
            language = match.group(1) or 'code'
            code = match.group(2).strip()
            
            # Escape کردن کد برای HTML
            code_escaped = html.escape(code)
            
            # فرمت تلگرام برای کد
            return f'<pre><code class="language-{language}">{code_escaped}</code></pre>'
        
        # جایگزینی code blocks
        text = re.sub(code_block_pattern, replace_code_block, text)
        
        # الگوی inline code (`code`)
        inline_code_pattern = r'`([^`]+)`'
        
        def replace_inline_code(match):
            code = match.group(1)
            code_escaped = html.escape(code)
            return f'<code>{code_escaped}</code>'
        
        # جایگزینی inline codes
        text = re.sub(inline_code_pattern, replace_inline_code, text)
        
        return text
    
    def format_response_for_telegram(self, ai_response: str) -> str:
        """
        فرمت کردن پاسخ AI برای ارسال در تلگرام
        با تشخیص و فرمت کد + escape کردن کاراکترهای خاص
        
        Args:
            ai_response: پاسخ خام AI
            
        Returns:
            پاسخ فرمت شده برای تلگرام با HTML
        """
        # فرمت کردن کدها
        formatted = self.format_code_blocks(ai_response)
        
        # Escape کردن کاراکترهای HTML که خارج از تگ‌های code هستند
        # این کار باید با دقت انجام شه تا تگ‌های code رو خراب نکنه
        
        # برای سادگی، از html.escape استفاده نمی‌کنیم چون قبلاً در format_code_blocks انجام دادیم
        # فقط کاراکترهای خاص خارج از code blocks رو escape می‌کنیم
        
        # تبدیل bold (**text**) به HTML
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', formatted)
        
        # تبدیل italic (*text*) به HTML
        formatted = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', formatted)
        
        return formatted
    
    async def translate_text_to_persian(self, text: str, max_length: int = 500) -> str:
        """ترجمه متن انگلیسی به فارسی با استفاده از Gemini (async version)"""
        if not text or len(text.strip()) == 0:
            return text
        
        # محدود کردن طول متن برای ترجمه
        text_to_translate = text[:max_length]
        
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Translate this English text to Persian (Farsi). Only provide the Persian translation, nothing else:\n\n{text_to_translate}"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2048
                }
            }
            
            # استفاده از await برای فراخوانی async
            result = await asyncio.to_thread(self._make_api_request, payload)
            
            if result['success']:
                response_data = result['response'].json()
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    persian_text = response_data['candidates'][0]['content']['parts'][0]['text']

                    return persian_text.strip()
            
            logger.warning(f"⚠️ ترجمه ناموفق، بازگشت متن اصلی")
            return text  # بازگشت متن اصلی در صورت خطا
            
        except Exception as e:
            logger.error(f"❌ خطا در ترجمه متن: {e}")
            return text

    async def translate_multiple_texts(self, texts: List[str], max_length: int = 500) -> List[str]:
        """ترجمه چندین متن انگلیسی به فارسی در یک درخواست واحد"""
        if not texts:
            return []
        
        try:
            # آماده‌سازی متن‌ها برای ترجمه
            texts_to_translate = []
            for text in texts:
                if text and len(text.strip()) > 0:
                    texts_to_translate.append(text[:max_length])
                else:
                    texts_to_translate.append(text)
            
            # ساخت prompt برای ترجمه گروهی
            translation_prompt = """Translate the following English texts to Persian (Farsi). 
IMPORTANT: Return ONLY the Persian translations in numbered format like this:
1. First Persian translation
2. Second Persian translation  
3. Third Persian translation

Keep the exact same order. Here are the texts to translate:

"""
            
            for i, text in enumerate(texts_to_translate, 1):
                if text and len(text.strip()) > 0:
                    translation_prompt += f"{i}. {text}\n\n"
                else:
                    translation_prompt += f"{i}. [Empty text]\n\n"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": translation_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 4096
                }
            }
            
            # ارسال درخواست واحد
            result = await asyncio.to_thread(self._make_api_request, payload)
            
            if result['success']:
                response_data = result['response'].json()
                
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    persian_response = response_data['candidates'][0]['content']['parts'][0]['text']

                    
                    # پارس کردن پاسخ با روش قوی‌تر
                    import re
                    persian_translations = []
                    
                    # استفاده از regex برای پیدا کردن همه آیتم‌های شماره‌دار
                    pattern = r'(\d+)\.\s*([^0-9]*?)(?=\d+\.|$)'
                    matches = re.findall(pattern, persian_response, re.DOTALL | re.MULTILINE)
                    
                    for match in matches:
                        number, content = match
                        clean_content = content.strip()
                        if clean_content:
                            persian_translations.append(clean_content)
                    

                    
                    # تطبیق تعداد ترجمه‌ها با تعداد متون اصلی
                    if len(persian_translations) < len(texts):

                        
                        # تلاش برای ترجمه‌های از دست رفته به صورت جداگانه
                        missing_count = len(texts) - len(persian_translations)

                        
                        for i in range(len(persian_translations), len(texts)):
                            try:
                                single_translation = await self.translate_text_to_persian(texts[i])
                                persian_translations.append(single_translation)
                            except Exception as e:

                                persian_translations.append(texts[i])  # استفاده از متن اصلی
                    
                    # محدود کردن به تعداد اصلی متون
                    persian_translations = persian_translations[:len(texts)]
                    

                    return persian_translations
            
            logger.warning(f"⚠️ ترجمه گروهی ناموفق، بازگشت متون اصلی")
            return texts  # بازگشت متون اصلی در صورت خطا
            
        except Exception as e:
            logger.error(f"❌ خطا در ترجمه گروهی: {e}")
            return texts


class AIChatStateManager:
    """مدیریت state چت کاربران"""
    
    def __init__(self, db_manager):
        """مقداردهی state manager"""
        self.db = db_manager
        self._init_chat_state_table()
        logger.debug("✅ AIChatStateManager مقداردهی شد")
    
    def _init_chat_state_table(self):
        """ایجاد جدول state چت"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # ایجاد جدول state چت
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_chat_state (
                    user_id BIGINT PRIMARY KEY,
                    is_in_chat BOOLEAN DEFAULT FALSE,
                    last_message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            
            # ایجاد index برای بهبود performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_chat_state_user
                ON ai_chat_state(user_id, is_in_chat)
            ''')
            
            conn.commit()
            logger.debug("✅ جدول ai_chat_state ایجاد شد")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در ایجاد جدول chat state: {e}")
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def start_chat(self, user_id: int) -> bool:
        """شروع چت برای کاربر"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # PostgreSQL syntax
            cursor.execute('''
                INSERT INTO ai_chat_state (user_id, is_in_chat, message_count)
                VALUES (%s, TRUE, 0)
                ON CONFLICT (user_id) DO UPDATE SET
                    is_in_chat = TRUE,
                    last_message_time = CURRENT_TIMESTAMP,
                    message_count = 0
            ''', (user_id,))
            
            conn.commit()
            logger.info(f"✅ چت AI برای کاربر {user_id} شروع شد")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در شروع چت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def end_chat(self, user_id: int) -> bool:
        """پایان چت برای کاربر و پاک کردن تاریخچه"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE ai_chat_state
                SET is_in_chat = FALSE,
                    last_message_time = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            
            # پاک کردن تاریخچه چت
            if self.db:
                self.db.clear_chat_history(user_id)
            
            logger.info(f"✅ چت AI برای کاربر {user_id} پایان یافت و تاریخچه پاک شد")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در پایان چت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def is_in_chat(self, user_id: int) -> bool:
        """بررسی اینکه آیا کاربر در حالت چت است یا خیر"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT is_in_chat FROM ai_chat_state WHERE user_id = %s',
                (user_id,)
            )
            result = cursor.fetchone()
            
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"❌ خطا در بررسی state چت: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def increment_message_count(self, user_id: int) -> bool:
        """افزایش شمارنده پیام‌های کاربر در چت"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE ai_chat_state
                SET message_count = message_count + 1,
                    last_message_time = CURRENT_TIMESTAMP
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ خطا در آپدیت message count: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def get_chat_stats(self, user_id: int) -> Dict[str, Any]:
        """دریافت آمار چت کاربر"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT message_count, last_message_time FROM ai_chat_state WHERE user_id = %s',
                (user_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return {
                    'message_count': result[0],
                    'last_message_time': result[1]
                }
            return {'message_count': 0, 'last_message_time': None}
            
        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار چت: {e}")
            return {'message_count': 0, 'last_message_time': None}
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
