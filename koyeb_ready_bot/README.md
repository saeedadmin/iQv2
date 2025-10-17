# Telegram Bot برای Koyeb

ربات پیشرفته تلگرام با قابلیت دریافت سیگنال‌های ترید و پنل ادمین

## نصب و راه‌اندازی

### 1. Environment Variables

در Koyeb این متغیرها را تنظیم کنید:

```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMIN_USER_ID=YOUR_TELEGRAM_USER_ID  
APIFY_API_KEY=YOUR_APIFY_API_KEY
ENVIRONMENT=production
PORT=8000
```

### 2. Deployment در Koyeb

**Service Configuration:**
- Service Type: Web Service
- Build Command: `pip install -r requirements.txt`
- Run Command: `python telegram_bot.py`
- Port: 8000

**Health Check:**
- Path: `/health`
- Port: 8000

### 3. دستورات ربات

- `/start` - شروع ربات
- `/menu` - منوی اصلی  
- `/signals` - دریافت سیگنال‌های ترید
- `/admin` - پنل ادمین
- `/status` - وضعیت سیستم

## نویسنده

MiniMax Agent