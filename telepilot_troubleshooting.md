# راهنمای جامع رفع مشکل TelePilot Community Node

## تشخیص مشکل
طبق لاگ‌هایی که ارسال کردی:
```
n8n detected that some packages are missing
Unrecognized node type: @telepilotco/n8n-nodes-telepilot.teleport
```

## راه‌حل‌ها (به ترتیب اولویت)

### راه‌حل 1: نصب مجدد از UI (اولویت بالا)
1. **ورود به n8n**
   - https://iqv2.onrender.com
   - یوزرنیم: `iqv2admin`
   - پسورد: `Iqv2N8N!2024Secure`

2. **بررسی Community Nodes**
   - Settings → Community Nodes
   - اگه `@telepilotco/n8n-nodes-telepilot` موجوده → **حذفش کن**
   - صبر کن 30 ثانیه

3. **نصب مجدد**
   - "Install Community Node" کلیک کن
   - پکیج: `@telepilotco/n8n-nodes-telepilot` (دقیقاً همین)
   - ✅ تیک چک باکس
   - "Install" کلیک کن

4. **انتظار و Restart**
   - صبر کن 2-3 دقیقه
   - اگه "Restart required" دیدی → سرویس رو restart کن
   - یا خودت restart کن: Render Dashboard → Your Service → Deploy

### راه‌حل 2: Environment Variable (اگه روش 1 جواب نداد)
1. **Render Dashboard**
   - برو render.com dashboard
   - سرویس n8n رو انتخاب کن

2. **Environment Variables**
   - تب "Environment" کلیک کن
   - Variable جدید اضافه کن:
     - **Name**: `N8N_COMMUNITY_PACKAGES`
     - **Value**: `["@telepilotco/n8n-nodes-telepilot"]`

3. **Deploy**
   - "Deploy" کلیک کن
   - صبر کن 5-10 دقیقه تا deployment تموم بشه

### راه‌حل 3: بررسی Log‌های جدید
بعد از هر نصب، این Log‌ها رو چک کن:
```
✅ Community package @telepilotco/n8n-nodes-telepilot installed successfully
❌ Error installing community package: [ERROR_MESSAGE]
```

### راه‌حل 4: Manual Package Installation
اگه همه روش‌ها جواب نداد:

1. **SSH به Container** (اگه دسترسی داری)
2. **Manual Installation**:
```bash
cd /usr/src/app
npm install @telepilotco/n8n-nodes-telepilot
npm run build
```

## تست بعد از نصب

### 1. بررسی Node List
1. New Workflow بساز
2. Add Node کلیک کن
3. سرچ کن: `teleport` یا `telepilot`
4. باید این گزینه‌ها رو ببینی:
   - **TelePilot Trigger** (یا ähnlich)
   - **TelePilot Action** (یا ähnlich)

### 2. تست ساده workflow
اگه TelePilot nodes دیدی، این workflow رو بساز:

**Node 1: TelePilot Trigger**
- Resource: `Trigger`
- Operation: `Listen`
- Events: `updateNewMessage`
- Chat Filter: Add `@shervin_trading`

**Node 2: Set**
- Add field: `test` = `true`

## اگه هنوز کار نکرد

### بررسی Version Compatibility
```bash
# چک کن n8n version
curl -s https://iqv2.onrender.com/api/v1/version \
  -H "X-N8N-API-KEY: YOUR_API_KEY"
```

### Clean Installation
1. Workflow قدیمی رو پاک کن
2. Cache رو clear کن
3. Community node رو حذف کن
4. از اول نصب کن

## نکات مهم
- ✅ حتماً دقیقاً این پکیج رو استف کن: `@telepilotco/n8n-nodes-telepilot`
- ✅ بعد از نصب، صبر کن 2-3 دقیقه
- ✅ سرویس رو restart کن
- ✅ Render log‌ها رو چک کن

## Contact Info
اگه هیچ‌کدوم جواب نداد، این اطلاعات رو بفرست:
1. نسخه n8n (Settings → About)
2. Render logs کامل
3. Community Nodes list (Settings → Community Nodes)
4. Screenshots از workflow builder