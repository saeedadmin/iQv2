# راه‌حل قطعی مشکل Koyeb Deployment

## 🚨 مشکل: Koyeb نمی‌تواند دستور اجرا پیدا کند

## ✅ راه‌حل تضمینی (Step by Step)

### مرحله ۱: Repository Check در GitHub

1. **برو به GitHub repository خودت**
2. **مطمئن شو این فایل‌ها در ROOT directory موجود هستند:**
   - ✅ `Procfile`
   - ✅ `requirements.txt`
   - ✅ `telegram_bot.py`
   - ✅ `runtime.txt`

3. **اگر فایل‌ها موجود نیستند:**
   - فایل‌ها را از workspace کپی کن
   - Commit و push کن

### مرحله ۲: Koyeb Configuration دقیق

#### 🔧 Service Configuration:
```
Service name: telegram-bot
Region: Frankfurt
Service type: Web service
Instance type: Small
```

#### 🔧 Deployment Method:
```
GitHub repository: [لینک repository تو]
Branch: main (یا master)
Root directory: / (خالی بذار)
```

#### 🔧 Build Configuration:
```
Build command: pip install -r requirements.txt
Run command: python telegram_bot.py
```

#### 🔧 Environment Variables:
```
BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw
ADMIN_USER_ID=[شناسه تلگرام تو]
APIFY_API_KEY=apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc
ENVIRONMENT=production
PORT=8000
```

#### 🔧 Health Checks:
```
Health check path: /health
Port: 8000
Grace period: 60 seconds
```

### مرحله ۳: اگر بالایی کار نکرد

#### گزینه A: Repository جدید
1. **Repository جدید بساز در GitHub**
2. **فقط این فایل‌ها upload کن:**
   - `Procfile`
   - `requirements.txt`
   - `telegram_bot.py`
   - `runtime.txt`
   - `database.py`
   - `admin_panel.py`
   - `public_menu.py`
   - `keyboards.py`
   - `logger_system.py`
   - `ai_news.py`
   - `telegram_signal_scraper.py`
   - همه فایل‌های Python ضروری

#### گزینه B: Manual Upload
1. **فایل‌ها را zip کن**
2. **GitHub web interface استفاده کن**
3. **Upload files مستقیم**

### مرحله ۴: Alternative Deployment

#### Docker Method:
```
Service type: Docker
Build context: Git repository
Dockerfile: Dockerfile
Port: 8000
```

#### Manual Command:
```
Run command: python3 telegram_bot.py
```

## 🎯 تست نهایی

### پس از deployment موفق باید ببینی:

```
✅ Building application... SUCCESS
✅ Installing dependencies... SUCCESS  
✅ Starting application... SUCCESS
✅ Health check passed... SUCCESS
🚀 ربات راه‌اندازی شد!
```

### تست عملکرد:
1. **Health check**: `https://your-app.koyeb.app/health`
2. **Telegram bot**: پیام `/start` بفرست
3. **Logs**: در Koyeb باید پیام‌های موفقیت ببینی

## 🆘 اگر باز کار نکرد

### Repository ساده:
```
telegram-bot/
├── Procfile
├── requirements.txt
├── runtime.txt
└── telegram_bot.py
```

### Minimal Procfile:
```
web: python telegram_bot.py
```

### Minimal requirements.txt:
```
python-telegram-bot>=22.5
aiohttp>=3.8.0
```

## 📞 دریافت کمک

اگر همچنان مشکل داری:

1. **Screenshot از GitHub repository structure بفرست**
2. **Screenshot از Koyeb configuration بفرست**  
3. **Logs کامل Koyeb را copy کن**
4. **لینک GitHub repository بده**

---

**💡 نکته مهم**: Koyeb گاهی ۵-۱۰ دقیقه طول می‌کشد تا deployment کامل شود. صبر کن و logs را مشاهده کن.