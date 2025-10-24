# مراحل تایید حل شدن مشکل

## چک‌لیست مراحل بعد از نصب Community Node

### ✅ مرحله 1: بررسی نصب
1. وارد n8n شو: https://iqv2.onrender.com
2. برو **Settings → Community Nodes**
3. باید این رو ببینی:
   ```
   @telepilotco/n8n-nodes-telepilot (INSTALLED)
   ```

### ✅ مرحله 2: بررسی Node List
1. **New Workflow** بساز
2. **Add Node** کلیک کن
3. سرچ کن: `teleport` یا `telepilot`
4. باید این گزینه‌ها رو ببینی:
   - `TelePilot Trigger` یا `TelePilot Action`
   - اگه این گزینه‌ها رو دیدی → نصب موفق بوده!

### ✅ مرحله 3: تست Workflow ساده
اگه TelePilot nodes دیدی، این workflow رو بساز:

**Node 1 - TelePilot Trigger:**
- Resource: Trigger
- Operation: Listen  
- Events: updateNewMessage
- Chat Filter: @shervin_trading

**Node 2 - Set:**
- Add field: `test` = `true`

### ✅ مرحله 4: Save و Activate
1. **Save** کلیک کن
2. **Activate** کلیک کن
3. نباید خطا بگیری!

## اگه هنوز خطا داری

### خطا: "Unrecognized node type"
- Community Node هنوز درست نصب نشده
- مجدداً راه‌حل 1 رو انجام بده

### خطا: "Node not found"  
- Workflow قدیمی رو پاک کن
- Workflow جدید بساز

### خطا: "Workflow has no trigger node"
- یعنی TelePilot Trigger رو درست اضافه نکردی
- مجدداً Node 1 رو درست کن

## قدم بعدی بعد از تایید
وقتی همه چیز درست کار کرد:
1. Workflow اصلی کریپتو رو فعال کن (LA5wq5D83e1HI0lQ)
2. UserBot credentials رو اضافه کن
3. شروع به مانیتورینگ کانال‌ها کن!