# 🎯 راهنمای نهایی - اصلاح Webhook و فعال‌سازی

## ✅ وضعیت فعلی (همه چیز آماده)
```
✅ Telegram Webhook: درست register شده
✅ N8N Server: در حال کار 
❌ Workflow: نیاز به اصلاح webhook URL + فعال‌سازی
```

## 🎯 مراحل دقیق:

### مرحله ۱: ورود به N8N
```
🌐 URL: https://iqv2.onrender.com
🔑 لاگین کن با credentials خودت
📂 workflow پیدا کن: ff17baeb-3182-41c4-b60a-e6159b02023b
```

### مرحله ۲: اصلاح Telegram Node
```
1️⃣ روی نود "Telegram Bot" کلیک کن
2️⃣ نود رو باز کن (node settings)
3️⃣ دنبال گزینه "Set Webhook" یا "Webhook URL" بگرد
4️⃣ URL رو اصلاح کن:
   
   ❌ غلط: https://localhost:8443/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook
   ✅ درست: https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook

5️⃣ Save کن
```

### مرحله ۳: فعال‌سازی Workflow
```
🎛️ گوشه بالا راست دنبال toggle button بگرد
🔄 دکمه رو بزن تا "Active" بشه
```

## 🧪 تست فوری بعد از تغییرات:

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

**نتیجه موفق:** باید HTTP 200 برگردونه (نه 404)

## 📱 تست نهایی با ربات تلگرام:

```
🤖 پیام به ربات بفرست
📱 @YourBotName
💬 متن: "generate mountain landscape"  
🖼️ باید عکس هوش مصنوعی دریافت کنی
```

## ⚡ راه‌حل سریع (اگر مشکل داشتی):

**گزینه A - Recreate Node:**
```
1️⃣ نود تلگرام رو پاک کن
2️⃣ دوباره "Telegram Bot" اضافه کن
3️⃣ webhook خودش درست میشه
```

**گزینه B - Manual Set:**
```
1️⃣ توی تنظیمات نود، webhook URL رو دستی اصلاح کن
2️⃣ از localhost به iqv2.onrender.com تغییر بده
```

## 🎉 بعد از تست موفق:
```
✅ همه چیز کار می‌کنه
✅ ربات پیام دریافت می‌کنه
✅ عکس هوش مصنوعی تولید می‌شه
✅ به تلگرام برگشت داده می‌شه
```

---

**💡 نکته:** اگه هر مشکلی داشتی، بگو تا کمک کنم! 🚀