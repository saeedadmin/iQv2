# راهنمای Troubleshooting برای نصب TelePilot

## مشکل 1: Package Install Failed

### علائم:
- Render logs: `npm install failed`
- Environment variable values not applying

### راه‌حل:
1. **همه متغیرها رو پاک کن**
2. **فقط این یکی رو اضافه کن:**
   ```
   Name: N8N_COMMUNITY_PACKAGES
   Value: ["@telepilotco/n8n-nodes-telepilot"]
   ```
3. **Deploy کن و صبر کن**
4. **بعد بقیه متغیرها رو یکی یکی اضافه کن**

## مشکل 2: Nodes Not Recognized

### علائم:
- Workflow error: `Unrecognized node type: @telepilotco/n8n-nodes-telepilot.teleport`
- Add Node dialog: TelePilot options ندیده میشه

### راه‌حل:
1. **Service restart کن** (Dashboard → Deploy)
2. **Browser cache clear کن**
3. **دوباره login کن** به n8n
4. **Check Settings → Community Nodes** (باید installed نشون بده)

## مشکل 3: Build Failed

### علائم:
- Render logs: `Building n8n failed`
- Service stuck in deployment

### راه‌حل:
1. **متغیر رو temporary remove کن**
2. **Default value اضافه کن:**
   ```
   Name: N8N_COMMUNITY_PACKAGES
   Value: []
   ```
3. **Deploy کن**
4. **بعد community package اضافه کن**

## راه‌حل نهایی: Manual Installation

### اگه همه روش‌ها جواب نداد:

#### روش SSH (Advanced):
```
1. Render Dashboard → Deployments → Latest → Console
2. یا SSH command:
ssh user@service-url
cd /usr/src/app
npm install @telepilotco/n8n-nodes-telepilot
npm run build
pm2 restart all
```

#### روش Package.json Update:
package.json پروژه رو آپدیت کن:
```json
{
  "dependencies": {
    "n8n": "^1.117.0",
    "@telepilotco/n8n-nodes-telepilot": "^0.5.2"
  }
}
```

## چک‌لیست رفع مشکل

### قبل از شروع:
- ✅ n8n version 1.117.0+ (check via Settings → About)
- ✅ Service running on latest commit
- ✅ Environment variables syntax correct

### بعد از installation:
- ✅ Community Nodes settings shows installed
- ✅ Node search includes "teleport"
- ✅ Workflow saves without errors
- ✅ TelePilot credentials can be configured

### اگه هنوز کار نمی‌کرد:
1. **UserBot credentials رو check کن** (+989025988819, @crypto_iq)
2. **Network connectivity** چک کن (Telegram API access)
3. **Logs بررسی کن** برای detailed errors
4. **Alternative workflow** بساز برای test (بدون UserBot)

## نکته مهم:
اگه TelePilot نصب نشد، **استفاده از Telegram Bot API** هنوز بهترین گزینه هست:
- Native n8n support
- سریع‌تر setup
- پایدارتر
- کافی برای monitoring @shervin_trading و @uniopn