# 🚀 راهنمای Deploy ربات تلگرام

این راهنما مراحل کامل انتقال ربات از محیط توسعه به محیط تولید را شرح می‌دهد.

## 📋 پیش‌نیازها

### حساب‌های مورد نیاز:
- ✅ [GitHub](https://github.com) (رایگان)
- ✅ [Supabase](https://supabase.com) (رایگان تا 500MB)
- ✅ [Railway](https://railway.app) (رایگان تا 512MB RAM)

---

## 🗃️ مرحله ۱: تنظیم Supabase Database

### ۱.۱ ایجاد پروژه جدید
```bash
1. وارد supabase.com شوید
2. "New Project" کلیک کنید
3. نام پروژه: telegram-bot-db
4. Password قوی انتخاب کنید
5. Region: West US (سریع‌تر)
6. منتظر تکمیل setup بمانید (~2 دقیقه)
```

### ۱.۲ دریافت Database URL
```bash
1. وارد Settings > Database شوید
2. Connection string > URI را کپی کنید
3. فرمت: postgresql://postgres:password@host:5432/postgres
```

### ۱.۳ انتقال داده‌ها (اختیاری)
اگر داده‌های مهمی در SQLite دارید:
```sql
-- در SQL Editor اجرا کنید
-- جداول به صورت خودکار ایجاد می‌شوند
```

---

## 📦 مرحله ۲: تنظیم GitHub Repository

### ۲.۱ ایجاد Repository جدید
```bash
1. وارد github.com شوید
2. "New repository" کلیک کنید
3. نام: telegram-bot-production
4. Public یا Private انتخاب کنید
5. "Create repository"
```

### ۲.۲ آپلود کدها
```bash
# در terminal محلی:
git init
git add .
git commit -m "Initial bot deployment setup"
git branch -M main
git remote add origin https://github.com/username/telegram-bot-production.git
git push -u origin main
```

---

## 🚂 مرحله ۳: تنظیم Railway Hosting

### ۳.۱ اتصال به GitHub
```bash
1. وارد railway.app شوید
2. "Deploy from GitHub repo" کلیک کنید
3. Repository خود را انتخاب کنید
4. "Deploy Now" کلیک کنید
```

### ۳.۲ تنظیم Environment Variables
در Railway Dashboard > Variables:
```env
BOT_TOKEN=1535325186:AAEWf9fPnJEW16ACEZEwmXIgbS2gZ5TGak8
ADMIN_USER_ID=327459477
DATABASE_URL=postgresql://postgres:password@host:5432/postgres
ENVIRONMENT=production
```

### ۳.۳ تنظیم Build Command
در Settings > Build:
```bash
Build Command: pip install -r requirements.txt
Start Command: python telegram_bot.py
```

---

## ⚡ مرحله ۴: تست و بررسی

### ۴.۱ بررسی Deploy
```bash
1. در Railway Dashboard > Deployments بررسی کنید
2. لاگ‌ها را بررسی کنید:
   - "✅ ربات راه‌اندازی شد!"
   - "📊 آمار: X کاربر، Y فعال"
```

### ۴.۲ تست عملکرد
```bash
1. در تلگرام /start بزنید
2. منوها را تست کنید
3. دکمه‌های مختلف را امتحان کنید
```

---

## 📊 مانیتورینگ و نگهداری

### مانیتورینگ Resources:
- **Railway Dashboard**: CPU, RAM, Network usage
- **Supabase Dashboard**: Database size, queries/hour
- **Bot Logs**: در Railway > Deploy Logs

### محدودیت‌های رایگان:
```
Railway: 512MB RAM, 1GB disk, $5 credit/month
Supabase: 500MB DB, 2GB bandwidth/month
GitHub: Unlimited public repos
```

### هشدارهای مهم:
```
⚠️ Railway: بعد از تمام شدن credit، service خاموش می‌شود
⚠️ Supabase: بعد از 500MB، نیاز به upgrade
⚠️ GitHub: private repos محدود
```

---

## 🔧 عیب‌یابی رایج

### مشکل: ربات start نمی‌شود
```
✅ بررسی Environment Variables
✅ بررسی Database URL
✅ بررسی Bot Token
✅ بررسی لاگ‌های Railway
```

### مشکل: Database connection error
```
✅ بررسی Supabase status
✅ بررسی connection string
✅ بررسی firewall settings
```

### مشکل: Out of memory
```
✅ کاهش logging
✅ بهینه‌سازی queries
✅ پاک کردن cache
```

---

## 📞 پشتیبانی

در صورت بروز مشکل:
1. **Railway**: Status page و documentation
2. **Supabase**: Community Discord
3. **Bot Issues**: GitHub Issues

---

## 🎯 مراحل بعدی (اختیاری)

### Custom Domain:
```bash
1. Railway > Settings > Domains
2. اضافه کردن custom domain
3. تنظیم DNS records
```

### Backup خودکار:
```bash
1. Supabase backup scheduling
2. Database dump scripts
3. Git automated backups
```

### Monitoring پیشرفته:
```bash
1. Sentry error tracking
2. Uptime monitoring
3. Performance metrics
```

---

> 🔥 **ربات آماده production است!**
> **تخمین هزینه ماهانه: $0 (در محدودیت‌های رایگان)**
