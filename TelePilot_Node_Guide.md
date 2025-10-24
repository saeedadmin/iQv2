# راهنمای یافتن Node های TelePilot در n8n

## قدم ۱: جستجوی دقیق TelePilot

در پنل n8n:

1. **روی Add Node کلیک کنید**
2. **در جستجو دقیقاً این رو بنویسید**:
   ```
   TelePilot
   ```
   (با حرف بزرگ T)

## قدم ۲: Node های موجود TelePilot

بعد از جستجو، باید این گزینه‌ها رو ببینید:

### 🔴 Trigger Nodes (شروع workflow):
- **TelePilot Trigger** - گرفتن همه events از تلگرام
- **TelePilot: On New Message** - وقتی پیام جدید اومد
- **TelePilot: On Chat Changed** - وقتی چت عوض شد

### 🔵 Action Nodes (ارسال/عملیات):
- **TelePilot: Send Message** - ارسال پیام
- **TelePilot: Send Photo** - ارسال عکس
- **TelePilot: Send Document** - ارسال فایل
- **TelePilot: Get Chat Info** - گرفتن اطلاعات چت

## قدم ۳: برای مانیتور کانال‌ها

برای پروژه شما این node مناسب هست:

**`TelePilot Trigger`**
- همه پیام‌های کانال‌های شما رو می‌گیره
- می‌تونید filter کنید روی کانال‌های خاص

## قدم ۴: پیکربندی اولیه

وقتی `TelePilot Trigger` رو انتخاب کردید:

```
Display Name: Crypto Monitor Bot
Phone: +989025988819
Username: crypto_iq
```

## قدم ۵: تست اولین Workflow

1. Node رو تنظیم کنید
2. Test Connection رو بزنید
3. کد تایید رو از اکانت @crypto_iq بگیرید

---

## اگر گزینه‌ها پیدا نشد:

این مراحل رو انجام بدید:

1. **n8n رو refresh کنید** (F5)
2. **دوباره جستجو کنید**: `TelePilot`
3. **ممکنه باید workflow رو ذخیره کنید و دوباره باز کنید**

## مرحله بعدی:
بعد از اینکه اولین TelePilot Trigger کار کرد، می‌ریم مرحله ۳: ساخت workflow تشخیص سیگنال