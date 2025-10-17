# 🚀 راهنمای نهایی Deployment در Koyeb

## 📦 فایل‌های آماده

بسته کامل ربات در <filepath>koyeb_ready_bot/</filepath> آماده شده است.

## 🎯 مراحل Deployment قطعی

### مرحله ۱: آپلود به GitHub

1. **Repository جدید بساز در GitHub**
2. **تمام فایل‌های داخل `koyeb_ready_bot` را آپلود کن**
3. **مطمئن شو این فایل‌ها در ریشه repository هستند:**
   - ✅ `Procfile`
   - ✅ `requirements.txt`
   - ✅ `runtime.txt`
   - ✅ `telegram_bot.py`
   - ✅ `Dockerfile`
   - ✅ `README.md`
   - ✅ `.gitignore`

### مرحله ۲: تنظیمات Koyeb

#### 🔧 Service Configuration:
```
Service name: telegram-bot
Region: Frankfurt (یا نزدیک‌ترین)
Service type: Web service
Instance type: Small
```

#### 🔧 Deployment Source:
```
GitHub repository: [لینک repository جدید]
Branch: main
Root directory: / (خالی بذار)
```

#### 🔧 Build Settings:
```
Build command: pip install -r requirements.txt
Run command: python telegram_bot.py
```

#### 🔧 Environment Variables (مهم!):
```
BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw
ADMIN_USER_ID=123456789
APIFY_API_KEY=apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc
ENVIRONMENT=production
PORT=8000
```

#### 🔧 Health Check:
```
Health check path: /health
Port: 8000
Grace period: 60 seconds
```

### مرحله ۳: Deploy!

1. **همه تنظیمات را دوباره بررسی کن**
2. **دکمه Deploy بزن**
3. **صبر کن تا build تمام شود (۳-۵ دقیقه)**

## ✅ بررسی موفقیت

### در Logs باید ببینی:
```
✅ Building application... SUCCESS
✅ Installing dependencies... SUCCESS
✅ Starting application... SUCCESS
🚀 ربات راه‌اندازی شد!
📊 آمار: X کاربر، Y فعال
🔗 آماده دریافت پیام...
```

### تست‌های نهایی:
1. **Health Check**: برو به `https://your-app.koyeb.app/health`
2. **Telegram Bot**: پیام `/start` بفرست
3. **سیگنال‌ها**: دستور `/signals` تست کن

## 🔄 اگر باز کار نکرد

### Alternative Method - Docker:

1. **در Koyeb:**
   - Service Type: **Docker**
   - Dockerfile: موجود است
   - Port: 8000

2. **یا Manual Command:**
   ```
   python3 telegram_bot.py
   ```

## 📞 Support

اگر همچنان مشکل داری:

1. **Screenshot از GitHub repository structure**
2. **Screenshot از Koyeb service configuration**
3. **Logs کامل از Koyeb**
4. **لینک GitHub repository**

## 🎉 نتیجه

با این بسته آماده، deployment باید **۱۰۰% موفق** باشد!

---

**فایل‌های آماده**: <filepath>koyeb_ready_bot/</filepath>  
**Archive**: <filepath>telegram_bot_koyeb_ready.tar.gz</filepath>