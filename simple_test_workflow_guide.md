# راهنمای ساخت Workflow ساده برای تست

## هدف: تست اینکه n8n درست کار می‌کنه

### مرحله 1: ورود به n8n
1. برو https://iqv2.onrender.com
2. یوزرنیم: `iqv2admin`
3. پسورد: `Iqv2N8N!2024Secure`

### مرحله 2: ساخت Workflow جدید
1. کلیک روی **"New Workflow"**
2. اسم workflow: `Simple Test`

### مرحله 3: اضافه کردن Node اول (Cron Trigger)
1. **Add Node** کلیک کن
2. سرچ کن: `cron`
3. انتخاب کن: **"Cron"**
4. تنظیمات:
   - **Mode**: Every Minute
   - یا دستی ست کن: `* * * * *`

### مرحاده 4: اضافه کردن Node دوم (Code)
1. از Cron، **Add Node** کلیک کن
2. سرچ کن: `code`
3. انتخاب کن: **"Code"** (نه Code ia)
4. در قسمت JavaScript بنویس:
```javascript
return [{
  json: {
    message: "Test successful!",
    timestamp: new Date().toISOString(),
    status: "Working"
  }
}];
```

### مرحله 5: ذخیره و تست
1. **Save** کلیک کن
2. **Execute Workflow** کلیک کن
3. نتیجه رو چک کن

## نتیجه مورد انتظار:
اگه درست کار کنه، یک JSON object با پیام "Test successful!" می‌بینی.

اگه این workflow درست کار کنه، یعنی n8n سالم هست و مشکل فقط از TelePilot community node هست.