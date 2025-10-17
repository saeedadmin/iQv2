# راهنمای دیپلوی در Koyeb

## مراحل دیپلوی در Koyeb

### ۱. تنظیمات Environment Variables

در پنل Koyeb، بخش Environment Variables را باز کنید و متغیرهای زیر را اضافه کنید:

```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ADMIN_USER_ID=YOUR_TELEGRAM_USER_ID
APIFY_API_KEY=YOUR_APIFY_API_KEY
ENVIRONMENT=production
```

**نکته مهم**: اگر BOT_TOKEN تنظیم نشده باشد، ربات شروع نخواهد شد.

### ۲. تنظیمات Service

- **Service Type**: Web Service
- **Port**: 8000 (خودکار از Procfile تشخیص داده می‌شود)
- **Health Check**: / یا /health
- **Instance Type**: حداقل Small instance

### ۳. تنظیمات Repository

- **GitHub Repository**: لینک repository خود
- **Branch**: main یا master
- **Build Command**: خودکار (از requirements.txt)
- **Run Command**: خودکار (از Procfile)

### ۴. فایل‌های ضروری

✅ `Procfile` - موجود است
✅ `requirements.txt` - موجود است  
✅ `runtime.txt` - موجود است
✅ Health Check Server - موجود است

### ۵. نکات مهم

1. **Conflict Error**: اگر خطای Conflict دریافت کردید:
   - همه deployments قدیمی را در Koyeb حذف کنید
   - فقط یک instance فعال نگه دارید
   - مطمئن شوید ربات روی محیط محلی خاموش است

2. **Health Check**: 
   - سرویس روی پورت 8000 در حال اجرا است
   - Endpoint های `/` و `/health` فعال است

3. **Logs**: 
   - در پنل Koyeb، بخش Logs را مشاهده کنید
   - اگر "✅ ربات راه‌اندازی شد!" را مشاهده کردید، همه چیز درست است

## خطاهای رایج و راه‌حل

### ❌ "no command to run your application"
**علت**: Procfile موجود نیست یا محتوای غلط دارد
**راه‌حل**: ✅ حل شده - Procfile درست تنظیم شده

### ❌ "Application exited with code 1"
**علت احتمالی**:
1. BOT_TOKEN تنظیم نشده
2. مشکل در import کردن modules
3. خطا در کد Python

**راه‌حل**:
1. Environment Variables را دوباره بررسی کنید
2. در Logs دنبال خطای دقیق بگردید

### ❌ "Conflict: terminated by other getUpdates request"
**علت**: چندین instance از ربات همزمان در حال اجرا است
**راه‌حل**: 
1. همه deployments قدیمی را حذف کنید
2. ربات محلی را خاموش کنید
3. فقط یک instance در Koyeb نگه دارید

## بررسی عملکرد

پس از deployment موفق:

1. **Health Check**: `https://your-app.koyeb.app/health` باید پاسخ OK بدهد
2. **Telegram**: ربات باید به پیام `/start` پاسخ دهد
3. **Logs**: باید پیام "✅ ربات راه‌اندازی شد!" را ببینید

## دستورات موجود

- `/start` - شروع ربات
- `/menu` - منوی اصلی
- `/signals` - دریافت سیگنال‌های تریدینگ
- `/admin` - پنل ادمین (فقط برای ادمین)
- `/status` - وضعیت سیستم

---

اگر همچنان مشکل دارید، لطفاً:
1. Environment Variables را دوباره بررسی کنید
2. Logs کامل Koyeb را بررسی کنید
3. متن خطای دقیق را ارسال کنید