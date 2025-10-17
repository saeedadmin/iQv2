# حل مشکل "no command to run your application" در Koyeb

## مشکل: Koyeb نمی‌تواند دستور اجرا را تشخیص دهد

### ✅ راه‌حل‌های مرتب بر اساس اولویت:

## 🥇 راه‌حل ۱: تنظیم مستقیم Run Command

**در پنل Koyeb:**

1. برو به **Service Settings**
2. تب **Build** را انتخاب کن
3. در قسمت **Run command** بنویس:
   ```
   python telegram_bot.py
   ```
4. **Deploy** کن

## 🥈 راه‌حل ۲: بررسی Branch و Directory

1. مطمئن شو که Koyeb از **branch صحیح** deploy می‌کند
2. **Root directory** باید `/` باشد (نه subdirectory)
3. در GitHub repository، Procfile باید در ریشه باشد

## 🥉 راه‌حل ۳: تغییر Service Type

**در تنظیمات Koyeb:**

1. **Service Type**: از Web Service به **Docker** تغییر بده
2. **Dockerfile** از repository استفاده می‌شود
3. **Port**: 8000

## 🏅 راه‌حل ۴: فایل‌های جایگزین

### آپشن A: استفاده از start.sh
در Run command بنویس:
```
bash start.sh
```

### آپشن B: استفاده از Python module
در Run command بنویس:
```
python -m telegram_bot
```

## 🔍 تشخیص عیب (Debugging)

### در Logs Koyeb دنبال این‌ها بگرد:

1. **"Building application"** - آیا build موفق است؟
2. **"Python version"** - آیا Python 3.12 استفاده می‌شود؟
3. **"Installing dependencies"** - آیا requirements.txt اجرا می‌شود؟
4. **"Starting application"** - آیا تا مرحله start می‌رود؟

### اگر Build ناموفق:
```
Build command: pip install -r requirements.txt
Run command: python telegram_bot.py
```

### اگر Dependencies ناموفق:
```
Build command: pip install --upgrade pip && pip install -r requirements.txt
Run command: python telegram_bot.py
```

## ⚙️ تنظیمات کامل Koyeb

### Service Configuration:
- **Name**: telegram-bot
- **Region**: Frankfurt (یا نزدیک‌ترین)
- **Instance Type**: Small
- **Ports**: 8000

### Environment Variables:
```
BOT_TOKEN=6595398909:AAHEY2c1iGPwAzJdKm8Qy5jAUCOjGN4UyDw
ADMIN_USER_ID=123456789
APIFY_API_KEY=apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc
ENVIRONMENT=production
PORT=8000
```

### Health Check:
- **Path**: `/health`
- **Port**: 8000
- **Grace Period**: 30 seconds

## 🆘 اگر همچنان کار نکرد:

### گزینه آخر: Manual Deployment

1. **فایل‌های ضروری را دوباره بررسی کن:**
   - ✅ Procfile
   - ✅ requirements.txt  
   - ✅ runtime.txt
   - ✅ telegram_bot.py

2. **Repository جدید بساز:**
   - فقط فایل‌های ضروری copy کن
   - Commit و push کن
   - Deploy جدید شروع کن

3. **Alternative Platform:**
   - Railway.app
   - Render.com  
   - Heroku

## 🎯 مراحل دقیق برای Deploy موفق:

### Step 1: Repository Check
```bash
# در GitHub repository ریشه بررسی کن:
ls -la
# باید ببینی:
# Procfile
# requirements.txt
# telegram_bot.py
# runtime.txt
```

### Step 2: Koyeb Configuration
1. **Github integration**: repository انتخاب کن
2. **Branch**: main یا master
3. **Build command**: (خالی بذار یا `pip install -r requirements.txt`)
4. **Run command**: `python telegram_bot.py`

### Step 3: Environment Variables
همان متغیرهایی که قبلاً گفتم را set کن

### Step 4: Deploy
Deploy کن و logs را مشاهده کن

## 📞 Support

اگر بعد از همه این‌ها باز کار نکرد:
1. Logs کامل Koyeb را copy کن
2. Screenshot از تنظیمات service بفرست  
3. لینک GitHub repository بده

---
**نکته مهم**: Koyeb گاهی ۵-۱۰ دقیقه طول می‌کشد تا deployment کامل شود.