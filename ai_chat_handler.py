#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت چت با هوش مصنوعی
نویسنده: MiniMax Agent
"""

import logging
import requests
import html
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class GeminiChatHandler:
    """مدیریت چت با Google Gemini API"""
    
    def __init__(self, api_key: str = None):
        """مقداردهی هندلر چت"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', 'AIzaSyA8HKbAXWjvh_cKQ8ynbyXztw6zIczelGk')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-2.0-flash-exp"
        
        # تنظیمات محدودیت
        self.max_message_length = 4000  # حداکثر طول پیام کاربر
        self.timeout = 30  # تایم‌اوت درخواست
        
        logger.info("✅ GeminiChatHandler مقداردهی شد")
    
    def send_message(self, user_message: str) -> Dict[str, Any]:
        """
        ارسال پیام به Google Gemini و دریافت پاسخ
        
        Args:
            user_message: پیام کاربر
            
        Returns:
            Dictionary با کلیدهای:
            - success: Boolean
            - response: متن پاسخ AI
            - tokens_used: تعداد توکن‌های استفاده شده
            - error: پیام خطا (در صورت وجود)
        """
        try:
            # محدود کردن طول پیام
            if len(user_message) > self.max_message_length:
                user_message = user_message[:self.max_message_length]
                logger.warning(f"⚠️ پیام کاربر به {self.max_message_length} کاراکتر محدود شد")
            
            # ساخت URL
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
            
            # ساخت payload
            payload = {
                "contents": [{
                    "parts": [{"text": user_message}]
                }]
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
    
    def format_response_for_telegram(self, ai_response: str) -> str:
        """
        فرمت کردن پاسخ AI برای ارسال در تلگرام
        با escape کردن کاراکترهای خاص برای HTML parse mode
        
        Args:
            ai_response: پاسخ خام AI
            
        Returns:
            پاسخ فرمت شده برای تلگرام
        """
        # Escape کردن کاراکترهای HTML
        formatted = html.escape(ai_response)
        
        # جایگزینی خط‌های خالی با فاصله مناسب
        formatted = formatted.replace('\n\n', '\n\n')
        
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
        """پایان چت برای کاربر"""
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
            logger.info(f"✅ چت AI برای کاربر {user_id} پایان یافت")
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
