# ربات تلگرام پیشرفته با پنل ادمین

ربات تلگرام قدرتمند با قابلیت‌های پیشرفته مدیریت کاربران، تحلیل TradingView و پنل ادمین کامل.

## ✨ ویژگی‌های کلیدی

### 🤖 عملکردهای اصلی
- **دستورات هوشمند**: `/start`, `/help`, `/status`
- **پردازش پیام‌ها**: تشخیص خودکار درخواست‌های تحلیل ارز
- **تحلیل TradingView**: دریافت آخرین تحلیل‌های ارزهای دیجیتال
- **پشتیبانی چندزبانه**: فارسی و انگلیسی

### 👨‍💼 پنل مدیریت پیشرفته
- **رابط کاربری شیشه‌ای**: پنل ادمین با InlineKeyboard
- **مدیریت سیستم**: نظارت بر منابع و وضعیت ربات
- **مدیریت کاربران**: آمار، بلاک/انبلاک، جستجو
- **پیام همگانی**: ارسال پیام به تمام کاربران
- **سیستم لاگ**: ثبت کامل فعالیت‌ها

### 💾 سیستم دیتابیس
- **SQLite/PostgreSQL**: پشتیبانی از دو نوع دیتابیس
- **مقیاس‌پذیری**: قابلیت تبدیل به PostgreSQL برای production
- **مدیریت کاربران**: ثبت خودکار و آمارگیری
- **سیستم لاگ**: ثبت تمام عملیات

### 📊 تحلیل TradingView
- **تحلیل زنده**: دریافت آخرین تحلیل‌ها از TradingView
- **فرمت‌های مختلف**: پشتیبانی از BTC، ETHUSDT، ETH/USDT
- **ارزهای محبوب**: Bitcoin, Ethereum, Solana, و بیش از 15 ارز دیگر
- **سیستم پشتیبان**: تحلیل‌های آفلاین در صورت عدم دسترسی

## 🚀 راه‌اندازی سریع

### پیش‌نیازها
- Python 3.9+
- Token ربات تلگرام از [@BotFather](https://t.me/BotFather)
- شناسه عددی ادمین (User ID)

### نصب

1. **Clone کردن پروژه:**
```bash
git clone https://github.com/saeedadmin/iQv2.git
cd iQv2
```

2. **نصب وابستگی‌ها:**
```bash
pip install -r requirements.txt
```

3. **تنظیم Environment Variables:**
```bash
# ایجاد فایل .env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_USER_ID=YOUR_USER_ID_HERE
```

4. **اجرای ربات:**
```bash
python telegram_bot.py
```

## 🌐 استقرار Production

### پلتفرم‌های پشتیبانی شده
- **Koyeb** (رایگان)
- **Railway** (رایگان با محدودیت)
- **Render** (رایگان با محدودیت)
- **Heroku** (پولی)

### تنظیمات Environment
متغیرهای زیر را در پلتفرم hosting تنظیم کنید:

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_telegram_user_id
DATABASE_URL=postgresql://... (اختیاری برای PostgreSQL)
PORT=8000 (برای WEB services)
```

### فایل‌های مهم
- **`Procfile`**: تنظیمات اجرا برای PaaS
- **`requirements.txt`**: وابستگی‌های Python
- **`web_server.py`**: HTTP server برای WEB services
- **`telegram_bot.py`**: فایل اصلی ربات

## 📋 دستورات ربات

### دستورات عمومی
- `/start` - شروع ربات و ثبت کاربر
- `/help` - راهنمای کامل
- `/status` - وضعیت ربات و کاربر

### دستورات ادمین
- `/admin` - دسترسی به پنل مدیریت
- `/broadcast` - پیام همگانی
- `/users` - مدیریت کاربران
- `/stats` - آمار سیستم

### تحلیل ارزها
فقط نام ارز را ارسال کنید:
- `BTC` یا `Bitcoin` - تحلیل بیت‌کوین
- `ETHUSDT` - تحلیل اتریوم
- `SOL/USDT` - تحلیل سولانا

## 🔧 ساختار پروژه

```
iQv2/
├── telegram_bot.py          # فایل اصلی ربات
├── web_server.py           # HTTP server برای hosting
├── database.py             # مدیریت دیتابیس SQLite
├── database_postgres.py    # مدیریت دیتابیس PostgreSQL
├── admin_panel.py          # پنل ادمین
├── public_menu.py          # منوهای عمومی
├── tradingview_analysis.py # تحلیل TradingView
├── user_management.py      # مدیریت کاربران
├── logger_system.py        # سیستم لاگ
├── requirements.txt        # وابستگی‌ها
├── Procfile               # تنظیمات deployment
└── README.md              # راهنمای پروژه
```

## 🤝 مشارکت

برای گزارش باگ یا پیشنهاد ویژگی جدید، لطفاً یک Issue ایجاد کنید.

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

---

**⚠️ نکته امنیتی**: هرگز اطلاعات حساس مانند Token ربات را در کد یا فایل‌های عمومی قرار ندهید. همیشه از Environment Variables استفاده کنید.
