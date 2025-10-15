# راهنمای دیپلوی در Koyeb

## متغیرهای محیطی مورد نیاز

برای عملکرد صحیح ربات در محیط production Koyeb، متغیرهای زیر را باید تنظیم کنید:

### متغیرهای اجباری:
- `BOT_TOKEN`: توکن ربات تلگرام
- `ADMIN_USER_ID`: ID عددی ادمین ربات
- `ENVIRONMENT`: حتماً روی `production` تنظیم کنید

### متغیرهای اختیاری:
- `KOYEB_PUBLIC_DOMAIN`: دامنه عمومی app شما در کایب (مثل: `my-app-name.koyeb.app`)

## مراحل دیپلوی:

### 1. تنظیم متغیرهای محیطی در Koyeb:
```
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=327459477
ENVIRONMENT=production
KOYEB_PUBLIC_DOMAIN=your-app-name.koyeb.app
```

### 2. بعد از دیپلوی:
- بررسی کنید که ربات بدون خطا شروع شده
- تست کنید عملکرد ربات را
- health check endpoint در دسترس است: `https://your-app.koyeb.app/health`

## تغییرات در این نسخه:

✅ **رفع مشکل Conflict:**
- از webhook به جای polling استفاده میشود
- مانع از اجرای چندتا instance همزمان میشود

✅ **بهبود Performance:**
- webhook سریعتر و کارآمدتر از polling است
- مصرف resource کمتری دارد

✅ **Monitoring:**
- Health check endpoint اضافه شده
- لاگ‌های بهتر برای troubleshooting

## Troubleshooting:

### اگر ربات پاسخ نمیدهد:
1. بررسی کنید `ENVIRONMENT=production` تنظیم شده باشد
2. بررسی کنید `KOYEB_PUBLIC_DOMAIN` درست تنظیم شده باشد
3. لاگ‌های Koyeb را بررسی کنید
4. health check endpoint را تست کنید

### اگر خطای Conflict هنوز وجود دارد:
1. instance قدیمی را کاملاً stop کنید
2. redeploy کنید
3. صبر کنید تا webhook کاملاً راه‌اندازی شود (2-3 دقیقه)
