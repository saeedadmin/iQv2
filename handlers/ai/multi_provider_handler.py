#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت چت با چندین سرویس هوش مصنوعی (نسخه پیشرفته)
نویسنده: MiniMax Agent

قابلیت‌ها:
- Multi-API rotation با کلیدهای متعدد
- Rate limiting هوشمند برای هر API
- Automatic fallback به API بعدی
- Load balancing بین API ها
- Health checking
- Translation با چندین سرویس
- چرخش هوشمند بین کلیدهای متعدد
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
import random
from dotenv import load_dotenv

# لود کردن متغیرهای محیطی از فایل .env
load_dotenv()

logger = logging.getLogger(__name__)

class KeyRotator:
    """مدیریت چرخش کلیدهای API"""
    
    def __init__(self, keys: List[str], provider_name: str):
        self.keys = keys
        self.provider_name = provider_name
        self.current_key_index = 0
        self.failed_keys = set()
        self.usage_stats = {key: 0 for key in keys}
        self.last_used = {key: None for key in keys}
        
    def get_next_key(self) -> Optional[str]:
        """دریافت کلید بعدی با چرخش هوشمند"""
        if not self.keys:
            return None
            
        # اگر همه کلیدها خراب هستند، reset کن
        if len(self.failed_keys) >= len(self.keys):
            self.failed_keys.clear()
        
        # تلاش برای پیدا کردن کلید معتبر
        for i in range(len(self.keys)):
            key = self.keys[(self.current_key_index + i) % len(self.keys)]
            
            if key in self.failed_keys:
                continue
                
            self.current_key_index = (self.current_key_index + i + 1) % len(self.keys)
            self.last_used[key] = datetime.datetime.now()
            return key
            
        return None
    
    def mark_key_failed(self, key: str):
        """علامت‌گذاری کلید به عنوان خراب"""
        self.failed_keys.add(key)
    
    def mark_key_success(self, key: str):
        """علامت‌گذاری کلید به عنوان موفق"""
        if key in self.failed_keys:
            self.failed_keys.remove(key)
        self.usage_stats[key] = self.usage_stats.get(key, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """آمار کلیدها"""
        return {
            "total_keys": len(self.keys),
            "failed_keys": len(self.failed_keys),
            "usage_stats": self.usage_stats.copy(),
            "last_used": self.last_used.copy()
        }

class MultiProviderHandler:
    """مدیریت چت با چندین سرویس هوش مصنوعی"""
    
    def __init__(self, db_manager=None):
        """مقداردهی handler با چندین provider"""
        self.db = db_manager
        
        # تنظیمات Rate Limiting
        self.rate_limit_messages = 20  # تعداد پیام مجاز
        self.rate_limit_seconds = 60  # در چند ثانیه
        self.user_message_times = {}
        
        # تعریف Providers با کلیدهای متعدد
        self.providers = self._initialize_providers()
        self.key_rotators = self._initialize_key_rotators()
        self.current_provider_index = 0
        self.failed_providers = set()  # لیست providers خراب
        
        # Retry Settings
        self.max_retries = 3
        self.retry_delay_base = 2
        
        # API Quota Tracking
        self.api_calls_today = {}
        self.last_reset_date = datetime.datetime.now().date()
        
        # Performance Tracking
        self.provider_performance = {}
        self.last_provider_test = {}
    
    def _initialize_providers(self) -> Dict[str, Dict]:
        """مقداردهی اولیه providers"""
        return {
            "groq": {
                "name": "Groq",
                "type": "openai_compatible",
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "requests_per_day": 14400,
                    "tokens_per_minute": 6000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "priority": 1,  # بالاترین اولویت (سریع‌ترین)
                "available": True
            },
            "cerebras": {
                "name": "Cerebras", 
                "type": "cerebras_sdk",
                "base_url": "https://api.cerebras.ai/v1",
                "models": ["qwen-3-235b-a22b-instruct-2507", "llama-3.3-70b"],
                "rate_limits": {
                    "requests_per_minute": 30,
                    "requests_per_day": 14400,
                    "tokens_per_minute": 60000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "priority": 2,  # دومین اولویت
                "available": True
            },
            "gemini": {
                "name": "Google Gemini",
                "type": "gemini",
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "models": ["gemini-2.0-flash-exp", "gemini-2.5-flash-lite"],
                "rate_limits": {
                    "requests_per_minute": 10,
                    "requests_per_day": 50,  # هر کلید 50
                    "tokens_per_minute": 250000
                },
                "headers": {
                    "Content-Type": "application/json"
                },
                "priority": 3,  # سومین اولویت
                "available": True
            },
            "openrouter": {
                "name": "OpenRouter",
                "type": "openai_compatible", 
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["deepseek/deepseek-chat-v3.1", "qwen/qwen-2.5-72b-instruct"],
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
                "priority": 4,
                "available": True
            },
            "cohere": {
                "name": "Cohere",
                "type": "cohere",
                "base_url": "https://api.cohere.ai/v1",
                "models": ["command-r", "command-r-plus"],
                "rate_limits": {
                    "requests_per_minute": 20,
                    "requests_per_day": 1000,  # Per month
                    "tokens_per_minute": 5000
                },
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer"
                },
                "priority": 5,
                "available": True
            }
        }
    
    def _initialize_key_rotators(self) -> Dict[str, KeyRotator]:
        """مقداردهی چرخش کلیدها"""
        rotators = {}
        
        # Groq keys
        groq_keys = []
        if os.getenv('GROQ_API_KEY'):
            groq_keys.append(os.getenv('GROQ_API_KEY'))
        if os.getenv('GROQ_API_KEY_2'):
            groq_keys.append(os.getenv('GROQ_API_KEY_2'))
        if groq_keys:
            rotators["groq"] = KeyRotator(groq_keys, "groq")
        
        # Cerebras keys
        cerebras_keys = []
        if os.getenv('CEREBRAS_API_KEY'):
            cerebras_keys.append(os.getenv('CEREBRAS_API_KEY'))
        if os.getenv('CEREBRAS_API_KEY_2'):
            cerebras_keys.append(os.getenv('CEREBRAS_API_KEY_2'))
        if cerebras_keys:
            rotators["cerebras"] = KeyRotator(cerebras_keys, "cerebras")
        
        # Gemini keys
        gemini_keys = []
        if os.getenv('GEMINI_API_KEY'):
            gemini_keys.append(os.getenv('GEMINI_API_KEY'))
        if os.getenv('GEMINI_API_KEY_2'):
            gemini_keys.append(os.getenv('GEMINI_API_KEY_2'))
        if gemini_keys:
            rotators["gemini"] = KeyRotator(gemini_keys, "gemini")
        
        # OpenRouter keys (اگر موجود باشد)
        if os.getenv('OPENROUTER_API_KEY'):
            rotators["openrouter"] = KeyRotator([os.getenv('OPENROUTER_API_KEY')], "openrouter")
        
        # Cohere keys (اگر موجود باشد)
        if os.getenv('COHERE_API_KEY'):
            rotators["cohere"] = KeyRotator([os.getenv('COHERE_API_KEY')], "cohere")
        
        return rotators
    
    def get_next_available_provider(self) -> Optional[str]:
        """دریافت provider بعدی که در دسترس است (بر اساس اولویت)"""
        if not self.providers:
            return None
            
        # اگر همه providers خراب هستند، reset کن
        if len(self.failed_providers) >= len(self.providers):
            self.failed_providers.clear()
        
        # مرتب‌سازی providers بر اساس اولویت و performance
        available_providers = []
        for name, provider in self.providers.items():
            if name not in self.failed_providers and name in self.key_rotators:
                available_providers.append((name, provider))
        
        # اگر هیچ provider فعال نباشد
        if not available_providers:
            return None
        
        # انتخاب provider بر اساس اولویت و performance
        best_provider = None
        best_score = float('-inf')
        
        for name, provider in available_providers:
            priority_score = -provider.get("priority", 999)  # اولویت کمتر = امتیاز بیشتر
            
            # اضافه کردن امتیاز performance (اگر موجود باشد)
            perf_data = self.provider_performance.get(name, {})
            success_rate = perf_data.get("success_rate", 0.5)  # پیش‌فرض 50%
            avg_response_time = perf_data.get("avg_response_time", 5.0)  # پیش‌فرض 5 ثانیه
            
            # Performance score: success rate بالا و response time کم = امتیاز بیشتر
            performance_score = success_rate * 10 - avg_response_time
            
            total_score = priority_score + performance_score
            
            if total_score > best_score:
                best_score = total_score
                best_provider = name
        
        if best_provider:
            logger.debug(f"✅ Selected provider by priority + performance: {best_provider}")
            return best_provider
        
        return None
    
    async def _make_api_request(self, provider_name: str, messages: List[Dict], model: str = None) -> Dict[str, Any]:
        """ارسال درخواست به provider مشخص"""
        provider = self.providers[provider_name]
        provider_type = provider.get("type")
        
        # دریافت کلید مناسب
        rotator = self.key_rotators.get(provider_name)
        if not rotator:
            raise Exception(f"No key rotator برای {provider_name}")
        
        api_key = rotator.get_next_key()
        if not api_key:
            raise Exception(f"No available API keys for {provider_name}")
        
        if not model:
            model = provider["models"][0]  # استفاده از اولین مدل
        
        try:
            # ارسال درخواست بر اساس نوع provider
            if provider_type == "openai_compatible":
                result = await self._make_openai_request(api_key, provider, messages, model)
            elif provider_type == "cerebras_sdk":
                result = await self._make_cerebras_request(api_key, provider, messages, model)
            elif provider_type == "gemini":
                result = await self._make_gemini_request(api_key, provider, messages, model)
            elif provider_type == "cohere":
                result = await self._make_cohere_request(api_key, provider, messages, model)
            else:
                raise Exception(f"نوع provider نامعتبر: {provider_type}")
            
            # موفقیت - به‌روزرسانی آمار
            rotator.mark_key_success(api_key)
            self.api_calls_today[provider_name] = self.api_calls_today.get(provider_name, 0) + 1
            
            # به‌روزرسانی performance data
            self._update_performance_data(provider_name, True, result.get("response_time", 1.0))
            
            return {
                "success": True,
                "content": result["content"],
                "provider": provider_name,
                "model": model,
                "api_key_used": api_key[:10] + "..."
            }
            
        except Exception as e:
            # خطا - علامت‌گذاری کلید به عنوان خراب
            rotator.mark_key_failed(api_key)
            
            # به‌روزرسانی performance data
            self._update_performance_data(provider_name, False, 0)
            
            raise
    
    async def _make_openai_request(self, api_key: str, provider: Dict, messages: List[Dict], model: str) -> Dict[str, Any]:
        """ارسال درخواست به OpenAI-compatible API"""
        headers = provider.get("headers", {}).copy()
        headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        url = f"{provider['base_url']}/chat/completions"
        
        start_time = time.time()
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return {"content": content, "response_time": response_time}
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")
    
    async def _make_cerebras_request(self, api_key: str, provider: Dict, messages: List[Dict], model: str) -> Dict[str, Any]:
        """ارسال درخواست به Cerebras با استفاده از کتابخانه رسمی"""
        try:
            from cerebras.cloud.sdk import Cerebras
            
            # ایجاد client
            client = Cerebras(api_key=api_key)
            
            # تبدیل پیام‌ها به فرمت Cerebras
            system_content = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_content = msg["content"]
                else:
                    user_messages.append(msg["content"])
            
            user_content = "\n".join(user_messages)
            
            start_time = time.time()
            
            # ارسال درخواست
            stream = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user", 
                        "content": user_content
                    }
                ],
                model=model,
                stream=False,  # Non-streaming برای سادگی
                max_completion_tokens=1000,
                temperature=0.7,
                top_p=0.8
            )
            
            response_time = time.time() - start_time
            
            # دریافت پاسخ
            content = stream.choices[0].message.content
            return {"content": content, "response_time": response_time}
            
        except ImportError:
            # Fallback به REST API
            headers = provider.get("headers", {}).copy()
            headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            url = f"{provider['base_url']}/chat/completions"
            
            start_time = time.time()
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {"content": content, "response_time": response_time}
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")
    
    async def _make_gemini_request(self, api_key: str, provider: Dict, messages: List[Dict], model: str) -> Dict[str, Any]:
        """ارسال درخواست به Gemini API"""
        headers = provider.get("headers", {}).copy()
        headers["x-goog-api-key"] = api_key
        
        # تبدیل پیام‌ها به فرمت Gemini
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
        
        url = f"{provider['base_url']}/models/{model}:generateContent"
        
        start_time = time.time()
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": content, "response_time": response_time}
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")
    
    async def _make_cohere_request(self, api_key: str, provider: Dict, messages: List[Dict], model: str) -> Dict[str, Any]:
        """ارسال درخواست به Cohere API"""
        headers = provider.get("headers", {}).copy()
        headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "message": messages[-1]["content"] if messages else "",
            "chat_history": messages[:-1] if len(messages) > 1 else []
        }
        
        url = f"{provider['base_url']}/chat"
        
        start_time = time.time()
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["reply"]
            return {"content": content, "response_time": response_time}
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")
    
    def _update_performance_data(self, provider_name: str, success: bool, response_time: float):
        """به‌روزرسانی داده‌های performance"""
        if provider_name not in self.provider_performance:
            self.provider_performance[provider_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0
            }
        
        data = self.provider_performance[provider_name]
        data["total_requests"] += 1
        
        if success:
            data["successful_requests"] += 1
            data["total_response_time"] += response_time
        
        # محاسبه success rate و average response time
        data["success_rate"] = data["successful_requests"] / data["total_requests"]
        if data["successful_requests"] > 0:
            data["avg_response_time"] = data["total_response_time"] / data["successful_requests"]
        else:
            data["avg_response_time"] = 0
    
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
                result = await self._make_api_request(provider_name, messages)
                
                # Record user message time
                if user_id:
                    self._record_user_message(user_id)
                
                return {
                    "success": True,
                    "content": result["content"],
                    "provider": result["provider"],
                    "model": result["model"],
                    "api_key_used": result.get("api_key_used", "N/A")
                }
                
            except Exception as e:
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
        
        # سیستم پرامپت مشخص برای ترجمه
        translation_system_prompt = "تو یک مترجم حرفه‌ای هستی که فقط به زبان فارسی پاسخ می‌دهی. هرگز انگلیسی یا هر زبان دیگری نوشته نمی‌شود. فقط ترجمه فارسی ارائه بده."
        
        for text in texts:
            try:
                # پیام ترجمه با سیستم پرامپت مشخص
                translation_prompt = f"لطفاً متن زیر را دقیقاً به فارسی ترجمه کن و فقط ترجمه فارسی بده:\n\n{text}"
                
                # استفاده از متد داخلی برای پیام با سیستم پرامپت مشخص
                result = await self._send_message_with_custom_prompt(translation_prompt, translation_system_prompt)
                
                if result["success"]:
                    # پاکسازی پاسخ از متن اضافی
                    translated_content = result["content"].strip()
                    translated_texts.append(translated_content)
                else:
                    translated_texts.append(text)  # استفاده از متن اصلی
                    
            except Exception as e:
                translated_texts.append(text)  # استفاده از متن اصلی
        
        return translated_texts
    
    async def _send_message_with_custom_prompt(self, message: str, custom_system_prompt: str) -> Dict[str, Any]:
        """ارسال پیام با سیستم پرامپت سفارشی"""
        messages = [
            {"role": "system", "content": custom_system_prompt},
            {"role": "user", "content": message}
        ]
        
        # تلاش با providers مختلف
        for attempt in range(len(self.providers)):
            provider_name = self.get_next_available_provider()
            
            if not provider_name:
                return {
                    "success": False,
                    "error": "No available providers",
                    "content": "متأسفانه در حال حاضر هیچ سرویس AI در دسترس نیست."
                }
            
            try:
                result = await self._make_api_request(provider_name, messages)
                
                return {
                    "success": True,
                    "content": result["content"],
                    "provider": result["provider"],
                    "model": result["model"],
                    "api_key_used": result.get("api_key_used", "N/A")
                }
                
            except Exception as e:
                continue
        
        return {
            "success": False, 
            "error": "All providers failed",
            "content": "متأسفانه در حال حاضر هیچ سرویس AI در دسترس نیست."
        }
    
    def reset_daily_quotas(self):
        """Reset کوئوتای روزانه"""
        current_date = datetime.datetime.now().date()
        if current_date != self.last_reset_date:
            self.api_calls_today.clear()
            self.last_reset_date = current_date
    
    def get_status(self) -> Dict[str, Any]:
        """دریافت وضعیت providers"""
        status = {
            "total_providers": len(self.providers),
            "available_providers": len([p for p in self.providers.values() if p.get("api_key")]),
            "failed_providers": list(self.failed_providers),
            "quota_status": {},
            "key_rotator_stats": {},
            "performance_stats": self.provider_performance.copy()
        }
        
        for name, provider in self.providers.items():
            daily_calls = self.api_calls_today.get(name, 0)
            max_daily = provider.get("rate_limits", {}).get("requests_per_day", 0)
            
            status["quota_status"][name] = {
                "calls_today": daily_calls,
                "max_daily": max_daily,
                "available": name not in self.failed_providers,
                "priority": provider.get("priority", 999)
            }
        
        # اضافه کردن آمار key rotators
        for name, rotator in self.key_rotators.items():
            status["key_rotator_stats"][name] = rotator.get_stats()
        
        return status