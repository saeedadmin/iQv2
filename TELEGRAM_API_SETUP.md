# 📋 راهنمای تنظیم Telegram API برای دریافت سیگنال‌ها

## 🎯 هدف
برای دریافت آخرین سیگنال‌های واقعی از کانال‌های تلگرام، نیاز به **Telegram API credentials** داریم.

## 📝 مراحل دریافت API Credentials

### 1️⃣ **ورود به پورتال Telegram**
- برو به: https://my.telegram.org
- با شماره تلفن خودتون وارد بشید

### 2️⃣ **ایجاد اپلیکیشن جدید**
- بعد از ورود، روی **"API Development Tools"** کلیک کنید
- **Create new application** رو انتخاب کنید

### 3️⃣ **تکمیل فرم اپلیکیشن**
```
App title: Signal Bot
Short name: signalbot
URL: (می‌تونید خالی بذارید)
Platform: Desktop
Description: Bot for fetching trading signals
```

### 4️⃣ **دریافت Credentials**
بعد از ثبت، این اطلاعات رو دریافت می‌کنید:
- **`api_id`**: یک عدد مثل `12345678`
- **`api_hash`**: یک رشته مثل `1234567890abcdef1234567890abcdef`

## ⚙️ تنظیم در پروژه

### Environment Variables
این مقادیر رو در فایل `.env` قرار دهید:

```env
# Telegram API for Signal Fetching
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=1234567890abcdef1234567890abcdef
```

### در Koyeb
در پنل Koyeb، این environment variables رو اضافه کنید:
- `TELEGRAM_API_ID` = عدد api_id شما
- `TELEGRAM_API_HASH` = رشته api_hash شما

## 🔐 نکات امنیتی

⚠️ **هرگز** این اطلاعات رو public نکنید
⚠️ این credentials شخصی هستند و مخصوص اکانت شما
⚠️ با این credentials میشه به تمام پیام‌های تلگرام شما دسترسی داشت

## 🧪 تست عملکرد

بعد از تنظیم، ربات باید:
1. به کانال‌های `@Shervin_Trading` و `@uniopn` دسترسی پیدا کنه
2. آخرین 2 سیگنال از هر کانال رو دریافت کنه
3. سیگنال‌ها رو بدون لینک‌ها و ID های کانال نمایش بده

## ❌ مشکلات متداول

### "API credentials missing"
- مطمئن بشید `TELEGRAM_API_ID` و `TELEGRAM_API_HASH` تنظیم شده
- restart کنید service رو در Koyeb

### "telethon not available"  
- مطمئن بشید `telethon>=1.36.0` در requirements.txt هست
- redeploy کنید پروژه رو

### "Phone number verification required"
- اولین بار نیاز به verification code هست
- این فقط یکبار اتفاق می‌افته

## 📞 راهنمایی بیشتر

اگه مشکلی داشتید، مراحل رو دوباره چک کنید یا با admin تماس بگیرید.
