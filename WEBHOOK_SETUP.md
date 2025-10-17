# 🔗 تنظیم Webhook برای جلوگیری از Sleep در Koyeb

## 🎯 هدف
جلوگیری از خوابیدن سرویس کویب با استفاده از Webhook به جای Polling

## ⚙️ مراحل تنظیم

### 1️⃣ تنظیم Environment Variables در Koyeb

در **Koyeb Dashboard** > **Service Settings** > **Environment Variables**:

```env
BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw
ADMIN_USER_ID=327459477
USE_WEBHOOK=true
KOYEB_PUBLIC_DOMAIN=your-app-name.koyeb.app
PORT=8000
```

**⚠️ نکته مهم:** `your-app-name.koyeb.app` را با دامنه واقعی اپتان جایگزین کنید.

### 2️⃣ تنظیم Health Check در Koyeb

در **Service Settings** > **Health Checks**:

```
Health Check Path: /health
Port: 8000
Protocol: HTTP
Interval: 30 seconds
Timeout: 10 seconds
Unhealthy threshold: 3
Healthy threshold: 2
```

### 3️⃣ Redeploy Service

1. **Save Changes** در Environment Variables
2. **Redeploy** سرویس
3. منتظر بمانید تا Status به **Healthy** تغییر کند

## 🧪 تست کردن

### بررسی Endpoints:
- `https://your-app-name.koyeb.app/health` - وضعیت سرویس
- `https://your-app-name.koyeb.app/ping` - تست ساده
- `https://your-app-name.koyeb.app/wake` - بیدار کردن

### خروجی نمونه `/health`:
```json
{
  "status": "healthy",
  "service": "telegram-bot",
  "timestamp": "2025-10-18T00:42:59",
  "uptime": "running",
  "mode": "webhook"
}
```

## ✅ علائم موفقیت

در **Logs** باید این پیام‌ها را ببینید:

```
🔗 تنظیم Webhook Mode...
📡 تنظیم webhook: https://your-app.koyeb.app/webhook
✅ Webhook تنظیم شد!
🏃‍♂️ سرویس در حالت Webhook اجرا می‌شود...
🏓 Async keep-alive فعال شد
🔄 Webhook Mode: Service alive
```

## 🔄 بازگشت به Polling

اگر مشکلی پیش آمد، می‌توانید به Polling برگردید:

```env
USE_WEBHOOK=false
```

## 🆘 عیب‌یابی

### اگر ربات جواب نمی‌دهد:
1. لاگ‌های کویب را بررسی کنید
2. مطمئن شوید `KOYEB_PUBLIC_DOMAIN` درست است
3. Webhook URL را چک کنید: `/webhook`

### اگر Health Check fail می‌شود:
1. پورت `8000` باز باشد
2. `/health` endpoint در دسترس باشد
3. Response code `200` باشد

## 💡 مزایای Webhook نسبت به Polling

✅ **مصرف منابع کمتر** - فقط در صورت نیاز فعال می‌شود  
✅ **پاسخ‌دهی سریع‌تر** - بدون تأخیر polling  
✅ **مناسب برای Production** - استاندارد صنعتی  
✅ **جلوگیری از Sleep** - همیشه آماده دریافت requests  
✅ **کاهش API calls** - کمتر محدودیت Telegram API  

## 🚀 نتیجه

با این تنظیمات، سرویس شما:
- هرگز sleep نمی‌شود
- پاسخ‌دهی بهتری دارد  
- منابع کمتری مصرف می‌کند
- برای production آماده است

---

**🎯 حالا redeploy کنید و از عدم Sleep شدن سرویس لذت ببرید!**