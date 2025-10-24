# راهنمای سریع: Telegram Bot API برای Crypto Signals

## چرا Bot API بهتر از UserBot؟
- ✅ **نصب ساده**: native n8n node
- ✅ **پایدار**: بدون dependency issues  
- ✅ **مطمئن**: official Telegram API
- ✅ **سریع**: 5 دقیقه setup

## مرحله 1: ساخت Bot (3 دقیقه)

### 1.1 Chat با @BotFather
```
1. تلگرام باز کن
2. @BotFather سرچ کن
3. Start کلیک کن
```

### 1.2 ایجاد Bot
```
/newbot

اسم bot: Crypto Signal Monitor
username: crypto_signal_monitor_bot

⚠️ username باید unique باشه، اگه گرفته شد:
crypto_signal_monitor_bot_2025
```

### 1.3 یادداشت Bot Token
```
🎉 Bot created!
Token: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

⚠️ این token رو یادداشت کن!
```

## مرحله 2: اضافه کردن Bot به کانال‌ها (2 دقیقه)

### 2.1 @shervin_trading
```
1. @shervin_trading رو باز کن
2. Add Members کلیک کن
3. @crypto_signal_monitor_bot سرچ کن
4. Add کلیک کن
5. Admin permissions بده:
   ✅ Post Messages
   ✅ Edit Messages  
   ✅ Delete Messages
```

### 2.2 @uniopn
همین کار رو برای @uniopn هم انجام بده.

## مرحله 3: تست Bot

### 3.1 پیام تست
```
1. @crypto_signal_monitor_bot رو باز کن
2. /start بزن
3. باید پیام welcome بگیری
```

### 3.2 تست در کانال
```
1. @shervin_trading رو باز کن
2. پیام تست بنویس: "Test crypto signal"
3. اگه Bot پیام رو دید، درسته!
```

## مرحله 4: Workflow در n8n (5 دقیقه)

### 4.1 ورود به n8n
```
URL: https://iqv2.onrender.com
Username: iqv2admin
Password: Iqv2N8N!2024Secure
```

### 4.2 New Workflow
```
1. "New Workflow" کلیک کن
2. اسم: "Crypto Signal Monitor"
```

### 4.3 اضافه کردن Telegram Trigger
```
1. "Add Node" کلیک کن
2. سرچ کن: "telegram"
3. انتخاب کن: "Telegram Trigger"
4. Credentials → "Create New"
   - Bot Token: [TOKEN_که_از_BotFather_گرفتی]
5. Test Connection کلیک کن
```

### 4.4 تنظیمات Trigger
```
Update Type: Message
Chat Type: Public Channel
Events: All Updates
```

### 4.5 اضافه کردن Code Node برای Signal Detection
```
1. از Telegram Trigger، "Add Node" کلیک کن
2. سرچ کن: "code"
3. انتخاب کن: "Code"
4. JavaScript کد:
```

```javascript
const message = items.json.message;
const text = message?.text || message?.caption || "";
const lowerText = text.toLowerCase();

// کلمات کلیدی کریپتو
const keywords = [
  "entry", "stop", "tp", "take profit", 
  "لوریج", "سیگنال", "buy", "sell", "target",
  "binance", "btc", "eth", "crypto"
];

// پیدا کردن keywords
const foundKeywords = keywords.filter(keyword => 
  lowerText.includes(keyword.toLowerCase())
);

// محاسبه confidence
let confidence = Math.min(foundKeywords.length * 15, 60);

// اموجی‌های مهم
const importantEmojis = ["💎", "🚀", "🔥", "⚡", "📈", "📊"];
const foundEmojis = importantEmojis.filter(emoji => text.includes(emoji));
confidence += foundEmojis.length * 8;

// حداقل threshold
if (confidence >= 40) {
  // تمیز کردن پیام
  const cleanMessage = text
    .replace(/https?:\/\/\S+/g, "")
    .replace(/t\.me\/\S+/g, "")
    .replace(/@\w+/g, "")
    .replace(/#\w+/g, "")
    .replace(/\s+/g, " ")
    .trim();

  return [{
    json: {
      confidence: confidence,
      originalText: text,
      cleanText: cleanMessage,
      foundKeywords: foundKeywords,
      foundEmojis: foundEmojis,
      channel: message.chat?.title || message.chat?.username,
      date: new Date(message.date * 1000),
      messageId: message.message_id
    }
  }];
}

// اگه signal نیست، هیچ خروجی نده
return [];
```

### 4.6 Save و Test
```
1. Ctrl+S (Save)
2. "Execute Workflow" کلیک کن
3. در کانال @shervin_trading پیام با کلمات کلیدی بنویس
4. نتیجه رو ببین
```

## مرحله 5: ارسال به کاربران

### 5.1 اضافه کردن Send Message Node
```
1. از Code Node، "Add Node" کلیک کن
2. سرچ کن: "telegram send"
3. انتخاب کن: "Telegram"
4. عملیات: "Send a Message"
```

### 5.2 تنظیمات ارسال
```
Bot Token: [همان Bot Token]
Chat ID: [-1001234567890] (chat ID کانال یا گروه)
Message: 
🔔 **سیگنال کریپتو تشخیص داده شد**

📊 Confidence: {{$node["Code"].json["confidence"]}}%
🏷️ Keywords: {{$node["Code"].json["foundKeywords"].join(", ")}}

📢 {{$node["Code"].json["channel"]}}:
{{$node["Code"].json["cleanText"]}}

⏰ {{$node["Code"].json["date"]}}
```

## نتیجه نهایی
Workflow توی 10 دقیقه آماده می‌شه و:
- ✅ کانال‌های @shervin_trading و @uniopn رو monitor می‌کنه
- ✅ سیگنال‌های کریپتو رو تشخیص می‌ده
- ✅ پیام‌ها رو تمیز می‌کنه
- ✅ با confidence scoring ارسال می‌کنه

## قدم بعدی
بعد از تست موفق، می‌تونی:
1. Bot رو به کانال‌های بیشتری اضافه کنی
2. Database برای ذخیره history اضافه کنی
3. User subscription management بسازی
4. 2FA برای UserBot فعال کنی (امنیت)

**می‌خوای شروع کنیم؟** 🚀