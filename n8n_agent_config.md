# راهنمای تنظیم N8N AI Image Creator Agent

## اطلاعات Agent
- **نام**: Automated AI Image Creator
- **ID**: eQq68FzJwEitmGXl  
- **URL**: https://iqv2.onrender.com/workflow/eQq68FzJwEitmGXl

## تنظیمات مورد نیاز

### 1. Google Gemini API Key
```bash
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 2. Telegram Bot (اختیاری)
```bash
TELEGRAM_BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw
TELEGRAM_CHAT_ID=327459477
```

### 3. Image Generation Config
```bash
# اندازه تصویر (پیش‌فرض: 1080x1920)
IMAGE_WIDTH=1080
IMAGE_HEIGHT=1920

# مدل تصویر (flux, kontext, turbo, gptimage)
IMAGE_MODEL=flux

# کیفیت تصویر (low, medium, high)
IMAGE_QUALITY=high
```

## نحوه استفاده

### روش 1: N8N Chat Interface
1. وارد N8N شوید: https://iqv2.onrender.com
2. به Workflow ID: eQq68FzJwEitmGXl بروید
3. روی "Execute Workflow" کلیک کنید
4. Prompt تصویر خود را وارد کنید

### روش 2: Telegram Bot
1. به بات تلگرام پیام دهید
2. Prompt تصویر را بنویسید (مثل: "تصویر غروب دریا با کشتی سفید")
3. تصویر تولید شده را دریافت کنید

## مثال‌های Prompt

### ✅ مثال‌های خوب:
- "A serene mountain landscape at sunset with a small cabin"
- "Modern office workspace with laptop, coffee, and plants"
- "Abstract art with blue and gold colors in modern style"
- "Cartoon character of a friendly robot in space suit"

### ❌ مثال‌های بد:
- "Make me a picture" (خیلی کلی)
- "Something beautiful" (ابهام)
- "Image of [copyrighted character]" (مسائل حقوقی)

## عیب‌یابی

### خطاهای احتمالی:
1. **API Key Invalid**: کلید Gemini اشتباه
2. **Rate Limit**: زیاد از حد درخواست داده‌اید
3. **Network Error**: مشکل اتصال
4. **Invalid Prompt**: prompt نامفهوم

### حل مشکلات:
- API key را چک کنید
- مجوزهای Gemini را بررسی کنید
- از prompt‌های واضح استفاده کنید
- مدت صبر را افزایش دهید

## تنظیمات پیشرفته

### تغییر AI Model:
در workflow node "AI Agent - Create Image From Prompt":
- Google Gemini (پیش‌فرض)
- OpenAI DALL-E
- Microsoft Copilot
- سایر مدل‌های سازگار

### Custom Image Sizes:
در workflow node "Fields - Set Values":
- Instagram Post: 1080×1080
- Twitter Header: 1500×500  
- YouTube Thumbnail: 1280×720
- Custom: مقادیر دلخواه

## امنیت
- API keys را در environment variables ذخیره کنید
- از webhook URLs عمومی استفاده نکنید
- Rate limiting را فعال کنید