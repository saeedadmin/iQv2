# نحوه اضافه کردن TelePilot به package.json

## روش 1: اضافه کردن به Package.json (پیشنهادی)

### مرحله 1: Update package.json
package.json موجود رو update کن:

```json
{
  "name": "iqv2-n8n-bot",
  "version": "1.0.0", 
  "description": "n8n deployment for iQv2 Telegram Bot",
  "main": "index.js",
  "scripts": {
    "start": "n8n start",
    "dev": "npx n8n start --tunnel"
  },
  "dependencies": {
    "n8n": "^1.117.0",
    "@telepilotco/n8n-nodes-telepilot": "^0.5.2"
  },
  "engines": {
    "node": ">=20.0.0"
  }
}
```

### مرحله 2: Environment Variable هم اضافه کن
```
N8N_COMMUNITY_PACKAGES=["@telepilotco/n8n-nodes-telepilot"]
```

## تفاوت روش‌ها

| ویژگی | فقط Environment | Environment + Package.json |
|-------|-----------------|----------------------------|
| نصب | runtime (slow startup) | build time (fast startup) |
| Version control | ❌ | ✅ |
| Deterministic | ❌ | ✅ |
| Performance | کند (هر بار نصب) | سریع |
| Validation | کم | زیاد |

## روش اجرا

### گزینه A: هر دو اضافه کن (پیشنهادی)
```bash
# 1. package.json update کن
# 2. Git push کن
# 3. Environment variable اضافه کن
N8N_COMMUNITY_PACKAGES=["@telepilotco/n8n-nodes-telepilot"]
```

### گزینه B: فقط Environment (ساده)
```bash
# فقط environment variable
N8N_COMMUNITY_PACKAGES=["@telepilotco/n8n-nodes-telepilot"]
```

## توصیه من
**گزینه A** بهتره چون:
- Faster deployment
- Deterministic installation  
- Version control
- Better error handling

## نتیجه
```bash
# Package.json پیشنهادی:
{
  "dependencies": {
    "n8n": "^1.117.0",
    "@telepilotco/n8n-nodes-telepilot": "^0.5.2"
  }
}

# Environment Variable:
N8N_COMMUNITY_PACKAGES=["@telepilotco/n8n-nodes-telepilot"]
```

## مراحل اجرا
1. **package.json update کن** (TelePilot اضافه کن)
2. **Git commit & push** کن
3. **Environment variable اضافه کن** 
4. **Render auto-deploy** منتظر بشه
5. **Test** کن

**این روش fastest و most reliable هست!** 🚀