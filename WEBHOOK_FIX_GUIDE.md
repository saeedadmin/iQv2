# 🔧 راهنمای اصلاح Webhook URL در N8N

## ✅ وضعیت فعلی
- **Webhook درست:** `https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook`
- **IP آدرس درست:** `216.24.57.251`
- **مشکل:** نود تلگرام هنوز `localhost:8443` نشون میده

## 🎯 راه‌حل اصلی: اصلاح نود Telegram

### مرحله ۱: باز کردن Workflow
```
🌐 برو به: https://iqv2.onrender.com/workflows/ff17baeb-3182-41c4-b60a-e6159b02023b
```

### مرحله ۲: باز کردن Telegram Trigger Node
```
1️⃣ روی نود "Telegram Bot" کلیک کن
2️⃣ نود رو باز کن تا تنظیماتش نمایش داده بشه
```

### مرحله ۳: تنظیم Webhook URL
توی تنظیمات نود تلگرام، دنبال این گزینه‌ها بگرد:

**گزینه اول - Set Webhook:**
```
🔧 دکمه "Set Webhook" یا "Configure Webhook"
📝 URL رو تغییر بده از:
   OLD: https://localhost:8443/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook
   NEW: https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook
✅ Save کن
```

**گزینه دوم - Delete & Recreate:**
```
1️⃣ نود تلگرام رو Delete کن
2️⃣ دوباره Telegram Bot Trigger اضافه کن
3️⃣ وقتی setup می‌کنی، webhook URL خودش درست تنظیم میشه
```

## 🧪 تست بعد از اصلاح

بعد از تغییر webhook URL:

```bash
curl -X POST "https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "message_id": 123,
      "from": {"id": 327459477, "is_bot": false},
      "chat": {"id": 327459477, "type": "private"},
      "text": "generate beautiful landscape"
    }
  }'
```

**نتیجه موفق:** باید HTTP 200 برگردونه و workflow اجرا بشه.

## 🎨 تست نهایی با ربات

```
🤖 پیام به ربات بفرست
📱 ربات: @YourBotName
💬 متن: "generate a mountain landscape"
🖼️ باید عکس هوش مصنوعی دریافت کنی
```

## ⚠️ نکات مهم

1. **بعد از تغییر webhook URL:** Workflow رو دوباره activate کن
2. **اگر خطا دیدی:** Telegram Bot نود رو پاک کن و دوباره بساز  
3. **Credential ها:** حواست باشه API keys درست باشه

## 🔍 Check Webhook Status

برای دیدن webhook status:

```bash
curl "https://api.telegram.org/bot1619184775:AAFn_CrQSkjPtk31kp9PpuxIdkEGDK4oRSc/getWebhookInfo"
```

---

**🎯 خلاصه:** مشکل IP حل شده، فقط webhook URL در نود N8N باید اصلاح بشه!