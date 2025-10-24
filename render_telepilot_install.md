# راهنمای نصب TelePilot از طریق Render Environment Variables

## راه‌حل: Environment Variable Installation

### مرحله 1: اضافه کردن Environment Variable در Render

#### 1.1 ورود به Render Dashboard
```
1. برو https://dashboard.render.com
2. Sign in کن
3. سرویس iqv2-n8n-bot رو پیدا کن
4. کلیک روش کن
```

#### 1.2 Environment Tab
```
1. تب "Environment" کلیک کن
2. Scroll کن پایین تا "Environment Variables"
3. "Add Environment Variable" کلیک کن
```

#### 1.3 اضافه کردن Variable
```
Name: N8N_COMMUNITY_PACKAGES
Value: ["@telepilotco/n8n-nodes-telepilot"]
Type: Single
```

#### 1.4 اضافه کردن Variables دیگر (برای عملکرد بهتر)
```bash
# Variable 1
Name: N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS
Value: false
Type: Single

# Variable 2  
Name: N8N_RUNNERS_ENABLED
Value: true
Type: Single

# Variable 3
Name: N8N_BLOCK_ENV_ACCESS_IN_NODE
Value: false
Type: Single

# Variable 4
Name: N8N_GIT_NODE_DISABLE_BARE_REPOS
Value: true
Type: Single

# Variable 5 (اختیاری - برای debugging)
Name: N8N_LOG_LEVEL
Value: debug
Type: Single
```

#### 1.5 Save و Deploy
```
1. "Save Changes" کلیک کن
2. Render خودکار deployment رو شروع می‌کنه
3. صبر کن 5-10 دقیقه تا تموم بشه
```

### مرحله 2: بررسی Logs

#### 2.1 Logs Tab
```
1. تب "Logs" کلیک کن
2. صبر کن تا deployment finish بشه
3. دنبال این پیام‌ها بگرد:
```

#### 2.2 پیام‌های موفقیت‌آمیز
```bash
✅ Community package @telepilotco/n8n-nodes-telepilot installed successfully
✅ Building n8n
✅ n8n is ready
```

#### 2.3 اگه خطا دیدی
```bash
❌ Error installing community package
❌ npm install failed

راه‌حل: متغیرها رو پاک کن و دوباره امتحان کن
```

### مرحله 3: تست در n8n

#### 3.1 ورود به n8n
```
URL: https://iqv2.onrender.com
Username: iqv2admin
Password: Iqv2N8N!2024Secure
```

#### 3.2 بررسی Community Nodes
```
1. Settings → Community Nodes
2. باید این رو ببینی:
   @telepilotco/n8n-nodes-telepilot (INSTALLED)
```

#### 3.3 تست Node Availability
```
1. New Workflow → Add Node
2. سرچ کن: "teleport" یا "telepilot"
3. باید این گزینه‌ها رو ببینی:
   - TelePilot Trigger
   - TelePilot Action
```

### مرحله 4: تست Workflow

#### 4.1 Workflow ساده بساز
```
1. New Workflow → "TelePilot Test"
2. Add Node → "TelePilot Trigger"
3. Credentials:
   - Display Name: Crypto Monitor Bot
   - Phone: +989025988819
   - Username: crypto_iq
4. Add Node → "Set" (test)
5. Save & Activate
```

## راه‌حل جایگزین: Manual Installation

### اگه Environment Variable جواب نداد:

#### روش SSH (Advanced)
```bash
# Render Dashboard → Deployments → Latest → Console
# یا از طریق command line:

# ورود به container
cd /usr/src/app

# نصب community node
npm install @telepilotco/n8n-nodes-telepilot

# Build مجدد
npm run build

# Restart n8n
pm2 restart iqv2-n8n-bot
# یا
killall node
npx n8n start
```

#### روش Dockerfile (اگه نیاز بود)
Dockerfile پروژه رو آپدیت کن:
```dockerfile
FROM node:20-alpine

WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./
COPY n8n-nodes-telepilot/ ./n8n-nodes-telepilot/

# Install all packages including community node
RUN npm ci

# Set environment variable
ENV N8N_COMMUNITY_PACKAGES=[\"@telepilotco/n8n-nodes-telepilot\"]

# Expose port
EXPOSE 5678

# Start n8n
CMD [\"n8n\", \"start\"]
```

## Troubleshooting

### مشکل: Package Install Failed
```bash
❌ npm install @telepilotco/n8n-nodes-telepilot failed
```
**راه‌حل:**
1. Variable رو پاک کن
2. دوباره اضافه کن: `[\"@telepilotco/n8n-nodes-telepilot\"]`
3. Deploy مجدد

### مشکل: Node Not Recognized
```bash
❌ Unrecognized node type: @telepilotco/n8n-nodes-telepilot.teleport
```
**راه‌حل:**
1. Service رو restart کن
2. Browser cache رو clear کن
3. دوباره login کن

### مشکل: Build Failed
```bash
❌ Building n8n failed
```
**راه‌حل:**
1. Variable رو پاک کن
2. Default value اضافه کن: `[]`
3. Deploy کن
4. بعد community package اضافه کن

## نتیجه مورد انتظار

بعد از successful installation:
- ✅ Community Nodes settings نصب شده رو نشون بده
- ✅ Add Node dialog شامل TelePilot options باشه
- ✅ Workflow بدون خطا فعال شه
- ✅ UserBot login موفق باشه

## قدم بعدی

بعد از نصب موفق:
1. Workflow اصلی کریپتو رو activate کن
2. UserBot credentials رو تست کن
3. Channel monitoring شروع کن
4. Signal detection رو validate کن