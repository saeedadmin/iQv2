# مراحل تنظیم N8N AI Image Creator Agent

## مرحله 1: Google Gemini API Setup

### 1.1 Google AI Studio
1. به https://aistudio.google.com بروید
2. با حساب Google وارد شوید
3. روی "Get API Key" کلیک کنید
4. API Key جدید ایجاد کنید

### 1.2 تست API Key
```bash
curl -X POST \
  'https://generativelanguage.googleapis.com/v1/models/gemini-pro-vision:generateContent?key=YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Generate an image of a sunset over mountains"
      }]
    }]
  }'
```

## مرحله 2: Render Environment Variables

### 2.1 ورود به Render Dashboard
1. به https://dashboard.render.com بروید
2. Service: `iqv2-n8n-bot` را پیدا کنید
3. روی آن کلیک کنید

### 2.2 اضافه کردن Environment Variables
در بخش Environment، این متغیرها را اضافه کنید:

```bash
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Telegram Bot (اختیاری - اگر می‌خواهید از Telegram استفاده کنید)
TELEGRAM_BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw

# Image Generation Settings
IMAGE_WIDTH=1080
IMAGE_HEIGHT=1920
IMAGE_MODEL=flux
IMAGE_QUALITY=high

# AI Model Configuration
AI_MODEL_PROVIDER=google
AI_MODEL_NAME=gemini-pro-vision
```

### 2.3 ذخیره و Deploy
1. Environment variables را Save کنید
2. Service را Manual Deploy کنید

## مرحله 3: N8N Workflow Configuration

### 3.1 ورود به N8N
1. به https://iqv2.onrender.com بروید
2. با username/password وارد شوید
3. به Workflow ID: `eQq68FzJwEitmGXl` بروید

### 3.2 تنظیم Credentials
در workflow این nodes را بررسی کنید:

#### "Telegram Trigger" Node:
- Bot Token: `6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw`
- Chat ID: `327459477` (یا Chat ID خودتان)

#### "AI Agent - Create Image From Prompt" Node:
- API Key: از environment variable `GEMINI_API_KEY`
- Model: `gemini-pro-vision`
- Image Model: `flux`

#### "Telegram Response" Node:
- Bot Token: از Telegram trigger
- Chat ID: مشابه trigger

### 3.3 تنظیم Image Parameters
در "Fields - Set Values" node:
```json
{
  "imageWidth": 1080,
  "imageHeight": 1920,
  "imageModel": "flux",
  "imageQuality": "high"
}
```

## مرحله 4: تست Agent

### 4.1 تست در N8N
1. روی "Execute Workflow" کلیک کنید
2. Test prompt: "A peaceful mountain landscape with a lake"
3. صبر کنید تا تصویر تولید شود

### 4.2 تست در Telegram (اختیاری)
1. به بات تلگرام پیام دهید
2. Prompt بنویسید: "/generate A cat wearing sunglasses at the beach"
3. تصویر را دریافت کنید

## مرحله 5: مدیریت و نظارت

### 5.1 monitoring
- Execution logs را بررسی کنید
- API usage را پیگیری کنید
- Error handling را تست کنید

### 5.2 بهینه‌سازی
- Rate limiting تنظیم کنید
- Error handling بهبود دهید
- Image quality را بر اساس نیاز تنظیم کنید

## نکات مهم

### ✅ انجام دهید:
- API keys را امن نگه دارید
- Rate limiting فعال کنید
- Error handling مناسب داشته باشید
- Regular backup از workflows

### ❌ انجام ندهید:
- API keys را در کد hardcode نکنید
- از prompt‌های نامفهوم استفاده نکنید
- بدون تست deploy نکنید

## Support
- N8N Documentation: https://docs.n8n.io
- Google Gemini API: https://ai.google.dev
- Render Documentation: https://render.com/docs