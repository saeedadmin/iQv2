# راهنمای جامع جایگزین‌های TelePilot

## مشکل TelePilot
- ✅ Package فعال هست (نسخه 0.5.2)  
- ❌ مشکل نصب در n8n community node
- ❌ نیاز به binary dependencies (پیچیده)

## جایگزین‌های بهتر و ساده‌تر

### 1. 🟢 Telegram Bot API + HTTP Polling (پیشنهاد اول)

#### مزایا:
- نصب ساده (native n8n node)
- پایدارتر و امن‌تر
- نیاز به setup کمتر

#### محدودیت:
- فقط کانال‌هایی که bot عضو هست
- محدودیت rate limits

#### راه‌اندازی:
1. **@BotFather** در تلگرام:
   ```
   /newbot
   اسم: Crypto Monitor Bot
   username: crypto_monitor_bot
   ```
   Bot Token دریافت می‌کنی: `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

2. **Bot رو به کانال‌ها اضافه کن**:
   - @shervin_trading
   - @uniopn
   - (Bot باید admin باشه)

### 2. 🔵 Custom HTTP Request Node

#### برای monitoring کانال‌های public بدون bot:
```javascript
// HTTP Request Node (GET)
URL: https://api.telegram.org/bot[BOT_TOKEN]/getUpdates
Method: GET

// Response پردازش در Code Node
const updates = items.json.result || [];
const messages = updates
  .filter(update => update.message)
  .map(update => ({
    id: update.message.message_id,
    text: update.message.text || update.message.caption,
    date: new Date(update.message.date * 1000),
    from: update.message.from?.username || 'Unknown',
    chat: update.message.chat?.title || update.message.chat?.username
  }));

return messages.map(msg => ({ json: msg }));
```

### 3. 🟡 Alternative Community Nodes

#### 3.1 n8n-telegram-advanced
```bash
# Package name (اگه وجود داشته باشه)
n8n-nodes-telegram-advanced
```

#### 3.2 telegram-webhooks-nodes
```bash
n8n-nodes-telegram-webhooks
```

### 4. 🟠 Hybrid Solution

#### ایده: UserBot بساز با TelePilot + Bot برای forwarding

**Workflow:**
1. **TelePilot UserBot** (مانیتور کانال‌ها)
2. **Signal Detection** (پردازش پیام‌ها)
3. **Telegram Bot API** (ارسال به کاربران)

## پیشنهاد عملی: Bot API Only

### قدم 1: ساخت Bot
```
1. @BotFather باز کن
2. /newbot بزن
3. اسم: "Crypto Signal Monitor"
4. username: "crypto_signal_monitor_bot"
5. Bot Token رو یادداشت کن
```

### قدم 2: اضافه کردن به کانال‌ها
```
1. @shervin_trading رو باز کن
2. Add Member → @crypto_signal_monitor_bot
3. Give admin permission
4. @uniopn هم همین کار
```

### قدم 3: Workflow در n8n

**Node 1: Telegram Trigger**
- Bot Token: `[YOUR_BOT_TOKEN]`
- Update Type: `Message`
- Chat Type: `Public Channel` یا `Channel`

**Node 2: Signal Detection**
```javascript
const keywords = ["entry", "stop", "tp", "لوریج", "buy", "sell", "target"];
const text = items.json.message?.text || items.json.message?.caption || "";
const lowerText = text.toLowerCase();

let foundKeywords = [];
keywords.forEach(keyword => {
  if (lowerText.includes(keyword.toLowerCase())) {
    foundKeywords.push(keyword);
  }
});

let confidence = Math.min(foundKeywords.length * 20, 60);
if (confidence >= 40) {
  return [{
    json: {
      originalMessage: text,
      cleanedMessage: text.replace(/https?:\/\/\S+/g, ""),
      confidence: confidence,
      keywords: foundKeywords,
      channel: items.json.message?.chat?.title || items.json.message?.chat?.username,
      timestamp: new Date(items.json.message?.date * 1000)
    }
  }];
}
```

**Node 3: Send Message**
- To Chat: `[CHAT_ID]`
- Text: (formatted message)

## بررسی کدام راه‌حل انتخاب کنیم

### اگه می‌خوای **سریع و ساده**:
→ **Telegram Bot API** (گزینه 1)

### اگه **کانال‌های public** رو بدون bot می‌خوای:
→ **HTTP Request + Custom** (گزینه 2)

### اگه **UserBot قدرتمند** می‌خوای:
→ **TelePilot** با manual installation (راهنمای مجزا)

## توصیه من
**از Telegram Bot API شروع کن** چون:
- نصب 5 دقیقه
- پایدار و مطمئن
- Native support در n8n
- امکانات کافی برای سیگنال کریپتو

بعد اگه نیاز داشتی، TelePilot رو برای advanced features اضافه کنی.