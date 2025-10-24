# راهنمای مرحله ۲: نصب و پیکربندی TelePilot در n8n

## ۱. نصب Community Nodes
1. وارد n8n شید: https://iqv2.onrender.com
2. روی **Settings** کلیک کنید
3. در منوی سمت چپ روی **Community Nodes** کلیک کنید
4. در کادر **Package Name** این رو وارد کنید:
   ```
   @telepilotco/n8n-nodes-telepilot
   ```
5. روی **Install** کلیک کنید

## ۲. راه‌اندازی TelePilot Node
1. یک workflow جدید بسازید
2. روی **Add Node** کلیک کنید
3. در جستجو "TelePilot" بنویسید و **TelePilot Monitor** رو انتخاب کنید

## ۳. پیکربندی TelePilot
### مشخصات اکانت شما:
- یوزرنیم: @crypto_iq
- شماره: +989025988819

### تنظیمات Node:
```
Display Name: Crypto Monitor Bot
Phone: +989025988819
Username: crypto_iq
Session Name: crypto_bot_session
```

## ۴. تست اولیه
1. روی **Test Connection** کلیک کنید
2. اگه کد تایید خواسته شد، به تلگرام اکانت @crypto_iq برید
3. کد تایید رو وارد کنید

## ۵. تنظیم پیشرفته
### Intervals:
- Check Interval: 30 (ثانیه)
- Max Messages: 10

### Filters:
- Include: `@shervin_trading,@uniopn`
- Exclude: `@me`

## مرحله بعدی
بعد از اینکه تست موفق شد، می‌ریم مرحله ۳: ساخت workflow سیگنال تشخیص