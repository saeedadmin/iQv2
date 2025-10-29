#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت چت با چندین سرویس هوش مصنوعی (نسخه پیشرفته)
نویسنده: MiniMax Agent

قابلیت‌ها:
- Multi-API rotation (Groq, Cerebras, Gemini, OpenRouter)
- Rate limiting هوشمند برای هر API
- Automatic fallback به API بعدی
- Load balancing بین API ها
- Health checking
- Translation با چندین سرویس
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
import json

logger = logging.getLogger(__name__)

class MultiProviderHandler:
    """مدیریت چت با چندین سرویس هوش مصنوعی"""
    
    def __init__(self, db_manager=None):
        """مقداردهی handler با چندین provider"""
        self.db = db_manager
        
        # تنظیمات Rate Limiting
        self.rate_limit_messages = 20  # تعداد پیام مجاز
        self.rate_limit_seconds = 60  # در چند ثانیه
        self.user_message_times = {}
        
        # تعریف Providers
        self.providers = self._initialize_providers()
        self.current_provider_index = 0
        self.failed_providers = set()  # لیست providers خراب
        
        # Retry Settings
        self.max_retries = 3
        self.retry_delay_base = 2
        
        # API Quota Tracking
        self.api_calls_today = {}
        self.last_reset_date = datetime.datetime.now().date()
        
        logger.info("🚀 MultiProviderHandler راه‌اندازی شد")
        logger.info(f"📊 تعداد providers فعال: {len(self.providers)}")
    
    def _initialize_providers(self) -> Dict[str, Dict]:
        """مقداردهی اولیه providers"""
        return {
            "groq": {
                "name": "Groq",
                "type": "openai_compatible",
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                "api_key": os.getenv('GROQ_API_KEY'),
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "requests_per_day": 14400,
                    "tokens_per_minute": 6000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "available": True
            },
            "cerebras": {
                "name": "Cerebras", 
                "type": "openai_compatible",
                "base_url": "https://api.cerebras.ai/v1",
                "models": ["gpt-oss-120b", "llama-3.3-70b"],
                "api_key": os.getenv('CEREBRAS_API_KEY'),
                "rate_limits": {
                    "requests_per_minute": 30,
                    "requests_per_day": 14400,
                    "tokens_per_minute": 60000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "available": True
            },
            "gemini": {
                "name": "Google Gemini",
                "type": "gemini",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "models": ["gemini-2.0-flash-exp", "gemini-2.5-flash-lite"],
                "api_key": os.getenv('GEMINI_API_KEY', 'AIzaSyA8HKbAXWjvh_cKQ8ynbyXztw6zIczelGk'),
                "rate_limits": {
                    "requests_per_minute": 10,
                    "requests_per_day": 50,
                    "tokens_per_minute": 250000
                },
                "headers": {
                    "Content-Type": "application/json"
                },
                "available": True
            },
            "openrouter": {
                "name": "OpenRouter",
                "type": "openai_compatible", 
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["deepseek/deepseek-chat-v3.1", "qwen/qwen-2.5-72b-instruct"],
                "api_key": os.getenv('OPENROUTER_API_KEY'),
                "rate_limits": {
                    "requests_per_minute": 20,
                    "requests_per_day": 50,
                    "tokens_per_minute": 8000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://yourapp.com",
                    "X-Title": "Telegram Bot"
                },
                "available": True
            },
            "cohere": {
                "name": "Cohere",
                "type": "cohere",
                "base_url": "https://api.cohere.ai/v1",
                "models": ["command-r", "command-r-plus"],
                "api_key": os.getenv('COHERE_API_KEY'),
                "rate_limits": {
                    "requests_per_minute": 20,
                    "requests_per_day": 1000,  # Per month
                    "tokens_per_minute": 5000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer"
                },
                "available": True
            }
        }
    
    def get_next_available_provider(self) -> Optional[str]:
        """دریافت provider بعدی که در دسترس است"""
        if not self.providers:
            return None
            
        # اگر همه providers خراب هستند، reset کن
        if len(self.failed_providers) >= len(self.providers):
            logger.warning("🔄 Reset کردن failed providers")
            self.failed_providers.clear()
        
        # چرخش بین providers
        for i in range(len(self.providers)):
            provider_name = list(self.providers.keys())[(self.current_provider_index + i) % len(self.providers)]
            provider = self.providers[provider_name]
            
            # بررسی موجود بودن API key
            if not provider.get("api_key"):
                logger.warning(f"⚠️ API key برای {provider_name} یافت نشد")
                continue
            
            # بررسی failed status
            if provider_name in self.failed_providers:
                logger.debug(f"⏭️ Skipping failed provider: {provider_name}")
                continue
            
            # بررسی quota
            if self._check_provider_quota(provider_name, provider):
                self.current_provider_index = (self.current_provider_index + i + 1) % len(self.providers)
                logger.debug(f"✅ Selected provider: {provider_name}")
                return provider_name
        
        return None
    
    def _check_provider_quota(self, provider_name: str, provider: Dict) -> bool:
        """بررسی کوئوتای provider"""
        # Simple quota check - می‌توانیم پیشرفته‌تر کنیم
        daily_calls = self.api_calls_today.get(provider_name, 0)
        max_daily = provider.get("rate_limits", {}).get("requests_per_day", 999999)
        
        return daily_calls < max_daily * 0.9  # 90% limit برای safety
    
    async def _make_api_request(self, provider_name: str, messages: List[Dict], model: str = None) -> Dict[str, Any]:
        """ارسال درخواست به provider مشخص"""
        provider = self.providers[provider_name]
        api_key = provider.get("api_key")
        base_url = provider.get("base_url")
        provider_type = provider.get("type")
        
        if not api_key:
            raise Exception(f"API key برای {provider_name} موجود نیست")
        
        if not model:
            model = provider["models"][0]  # استفاده از اولین مدل
        
        # تنظیم headers
        headers = provider.get("headers", {}).copy()
        if provider_type == "openai_compatible":
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider_type == "gemini":
            headers["x-goog-api-key"] = api_key
        elif provider_type == "cohere":
            headers["Authorization"] = f"Bearer {api_key}"
        
        # تنظیم payload بر اساس نوع provider
        if provider_type == "openai_compatible":
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            url = f"{base_url}/chat/completions"
            
        elif provider_type == "gemini":
            # Gemini format
            content = "\n".join([msg["content"] for msg in messages if msg["role"] != "system"])
            payload = {
                "contents": [{
                    "parts": [{"text": content}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 1000,
                    "temperature": 0.7
                }
            }
            url = f"{base_url}/models/{model}:generateContent"
            
        elif provider_type == "cohere":
            # Cohere format
            payload = {
                "model": model,
                "message": messages[-1]["content"] if messages else "",
                "chat_history": messages[:-1] if len(messages) > 1 else []
            }
            url = f"{base_url}/chat"
        
        # ارسال درخواست
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"🔄 Attempt {attempt + 1} for {provider_name}")
                
                response = requests.post(
                    url=url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # بررسی پاسخ
                if response.status_code == 200:
                    result = response.json()
                    
                    # Normalize response بر اساس نوع provider
                    if provider_type == "openai_compatible":
                        content = result["choices"][0]["message"]["content"]
                    elif provider_type == "gemini":
                        content = result["candidates"][0]["content"]["parts"][0]["text"]
                    elif provider_type == "cohere":
                        content = result["reply"]
                    
                    self.api_calls_today[provider_name] = self.api_calls_today.get(provider_name, 0) + 1
                    logger.info(f"✅ {provider_name} call successful")
                    
                    return {
                        "success": True,
                        "content": content,
                        "provider": provider_name,
                        "model": model
                    }
                
                elif response.status_code == 429:
                    # Rate limit
                    retry_after = int(response.headers.get("retry-after", 2))
                    logger.warning(f"⏳ Rate limit برای {provider_name}, retry بعد از {retry_after}s")
                    
                    # Mark as failed temporarily
                    self.failed_providers.add(provider_name)
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(min(retry_after, 30))
                        continue
                
                else:
                    logger.error(f"❌ {provider_name} API error: {response.status_code} - {response.text}")
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay_base * (2 ** attempt))
                        continue
                    
                    # Mark as failed
                    self.failed_providers.add(provider_name)
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                logger.error(f"❌ خطا در درخواست {provider_name}: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay_base * (2 ** attempt))
                    continue
                
                # Mark as failed
                self.failed_providers.add(provider_name)
                raise
        
        raise Exception(f"تمام تلاش‌ها برای {provider_name} ناموفق بود")
    
    async def send_message(self, message: str, user_id: int = None) -> Dict[str, Any]:
        """ارسال پیام با استفاده از provider موجود"""
        # بررسی rate limit کاربر
        if user_id and not self._check_user_rate_limit(user_id):
            return {
                "success": False,
                "error": "Rate limit exceeded for user",
                "content": "شما زیادی پیام فرستاده‌اید، لطفاً کمی صبر کنید."
            }
        
        # پیام سیستم برای راهنمایی AI
        system_prompt = "تو یک دستیار هوشمند هستی که به زبان فارسی پاسخ می‌دهی. پاسخ‌هایت مفید، دقیق و کوتاه باشد."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # تلاش با providers مختلف
        for attempt in range(len(self.providers)):
            provider_name = self.get_next_available_provider()
            
            if not provider_name:
                return {
                    "success": False,
                    "error": "No available providers",
                    "content": "متأسفانه در حال حاضر هیچ سرویس AI در دسترس نیست. لطفاً بعداً تلاش کنید."
                }
            
            try:
                logger.info(f"🎯 Trying provider: {provider_name}")
                result = await self._make_api_request(provider_name, messages)
                
                # Record user message time
                if user_id:
                    self._record_user_message(user_id)
                
                return {
                    "success": True,
                    "content": result["content"],
                    "provider": result["provider"],
                    "model": result["model"]
                }
                
            except Exception as e:
                logger.error(f"❌ Provider {provider_name} failed: {e}")
                continue
        
        return {
            "success": False, 
            "error": "All providers failed",
            "content": "متأسفانه در حال حاضر هیچ سرویس AI در دسترس نیست."
        }
    
    async def translate_multiple_texts(self, texts: List[str]) -> List[str]:
        """ترجمه گروهی متون به فارسی"""
        if not texts:
            return []
        
        translated_texts = []
        
        for text in texts:
            try:
                # پیام ترجمه
                translation_prompt = f"لطفاً متن زیر را به فارسی ترجمه کن:\n\n{text}"
                
                result = await self.send_message(translation_prompt)
                
                if result["success"]:
                    translated_texts.append(result["content"])
                else:
                    translated_texts.append(text)  # استفاده از متن اصلی
                    
            except Exception as e:
                logger.error(f"❌ خطا در ترجمه متن: {e}")
                translated_texts.append(text)  # استفاده از متن اصلی
        
        return translated_texts
    
    def _check_user_rate_limit(self, user_id: int) -> bool:
        """بررسی rate limit کاربر"""
        current_time = datetime.datetime.now()
        
        if user_id not in self.user_message_times:
            self.user_message_times[user_id] = []
        
        # حذف پیام‌های قدیمی
        cutoff_time = current_time - datetime.timedelta(seconds=self.rate_limit_seconds)
        self.user_message_times[user_id] = [
            t for t in self.user_message_times[user_id] 
            if t > cutoff_time
        ]
        
        # بررسی تعداد پیام‌ها
        message_count = len(self.user_message_times[user_id])
        return message_count < self.rate_limit_messages
    
    def _record_user_message(self, user_id: int):
        """ثبت پیام کاربر"""
        current_time = datetime.datetime.now()
        if user_id not in self.user_message_times:
            self.user_message_times[user_id] = []
        self.user_message_times[user_id].append(current_time)
    
    def reset_daily_quotas(self):
        """Reset کوئوتای روزانه"""
        current_date = datetime.datetime.now().date()
        if current_date != self.last_reset_date:
            self.api_calls_today.clear()
            self.last_reset_date = current_date
            logger.info("🔄 Daily quotas reset شد")
    
    def get_status(self) -> Dict[str, Any]:
        """دریافت وضعیت providers"""
        status = {
            "total_providers": len(self.providers),
            "available_providers": len([p for p in self.providers.values() if p.get("api_key")]),
            "failed_providers": list(self.failed_providers),
            "quota_status": {}
        }
        
        for name, provider in self.providers.items():
            daily_calls = self.api_calls_today.get(name, 0)
            max_daily = provider.get("rate_limits", {}).get("requests_per_day", 0)
            
            status["quota_status"][name] = {
                "calls_today": daily_calls,
                "max_daily": max_daily,
                "api_key_available": bool(provider.get("api_key")),
                "available": name not in self.failed_providers
            }
        
        return status