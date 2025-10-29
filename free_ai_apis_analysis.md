# 📋 تحلیل API های رایگان AI

## 🚀 بهترین گزینه‌ها برای کلیدهای رایگان:

### 1. **Groq** ⭐⭐⭐⭐⭐
- **محدودیت**: تا 14,400 درخواست/روز (بالا!)
- **مدل‌ها**: Llama, DeepSeek, Qwen
- **ثبت‌نام**: console.groq.com

### 2. **Cerebras** ⭐⭐⭐⭐⭐  
- **محدودیت**: 14,400 درخواست/روز، 1M tokens/روز
- **مدل‌ها**: GPT-OSS 120B, Llama 3.3, Qwen 3
- **ثبت‌نام**: cloud.cerebras.ai

### 3. **Google AI Studio (Gemini)** ⭐⭐⭐⭐
- **محدودیت**: 50-1000 درخواست/روز (بسته به مدل)
- **مدل‌ها**: Gemini 2.5 Pro, Flash, Flash-Lite
- **ثبت‌نام**: aistudio.google.com

### 4. **OpenRouter** ⭐⭐⭐
- **محدودیت**: 20/دقیقه، 50/روز (1000/روز با $10)
- **مدل‌ها**: DeepSeek, Llama, Mistral, Qwen
- **ثبت‌نام**: openrouter.ai

### 5. **Cohere** ⭐⭐⭐
- **محدودیت**: 20/دقیقه، 1000/ماه
- **مدل‌ها**: Command R, Aya Expanse
- **ثبت‌نام**: cohere.com

## 🎯 برنامه پیاده‌سازی:

### مرحله 1: Multi-API Rotation System
- ایجاد کلاس APIManager برای چرخش بین API ها
- اضافه کردن health check برای هر API
- Fallback system هنگام rate limit

### مرحله 2: پیکربندی API Keys
- جمع‌آوری کلیدهای کاربر از سایت‌های فوق
- ذخیره امن در environment variables

### مرحله 3: بهبود کد موجود
- جایگزینی GeminiChatHandler با MultiProviderHandler
- اضافه کردن logging و monitoring بهتر

## 🔥 نکته طلایی:
**Groq** و **Cerebras** هر کدام 14,400 درخواست/روز دارند که یعنی تقریباً 10 برابر Gemini رایگان!