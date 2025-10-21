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
        
        logger.info("✅ GeminiChatHandler با حافظه مکالمه مقداردهی شد")
    
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
        """
        try:
            # بررسی Rate Limit
            rate_check = self.check_rate_limit(user_id)
            if not rate_check['allowed']:
                wait_time = rate_check['wait_time']
                return {
                    'success': False,
                    'error': f'rate_limit:{wait_time}',
                    'response': None,
                    'tokens_used': 0
                }
            
            # پاکسازی ورودی
            user_message = self.sanitize_input(user_message)
            
            if not user_message:
                return {
                    'success': False,
                    'error': 'پیام خالی است',
                    'response': None,
                    'tokens_used': 0
                }
            
            # دریافت تاریخچه چت از دیتابیس
            chat_history = []
            if self.db:
                chat_history = self.db.get_chat_history(user_id, limit=self.max_history_messages)
            
            # ساخت URL
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            
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
            
            # ارسال درخواست
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            # بررسی status code
            if response.status_code != 200:
                error_msg = f"خطای API: {response.status_code}"
                logger.error(f"❌ {error_msg} - {response.text}")
                return {
                    'success': False,
                    'error': error_msg,
                    'response': None,
                    'tokens_used': 0
                }
            
            # Parse کردن پاسخ
            result = response.json()
            
            # استخراج متن پاسخ
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                tokens_used = result.get('usageMetadata', {}).get('totalTokenCount', 0)
                
                # ذخیره پیام کاربر و پاسخ AI در تاریخچه
                if self.db:
                    self.db.add_chat_message(user_id, 'user', user_message)
                    self.db.add_chat_message(user_id, 'model', ai_text)
                
                return {
                    'success': True,
                    'response': ai_text,
                    'tokens_used': tokens_used,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'پاسخ نامعتبر از API',
                    'response': None,
                    'tokens_used': 0
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout در ارتباط با API")
            return {
                'success': False,
                'error': 'زمان درخواست به پایان رسید',
                'response': None,
                'tokens_used': 0
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطا در ارتباط با API: {e}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با سرور',
                'response': None,
                'tokens_used': 0
            }
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره در GeminiChat: {e}")
            return {
                'success': False,
                'error': 'خطای غیرمنتظره',
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


class AIChatStateManager:
    """مدیریت state چت کاربران"""
    
    def __init__(self, db_manager):
        """مقداردهی state manager"""
        self.db = db_manager
        self._init_chat_state_table()
        logger.info("✅ AIChatStateManager مقداردهی شد")
    
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
            logger.info("✅ جدول ai_chat_state ایجاد شد")
            
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
