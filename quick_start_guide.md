# 🚀 راهنمای سریع شروع (10 دقیقه)

## بهترین راه‌حل: Telegram Bot API

### مزایا:
- ✅ نصب فوری (بدون community node)
- ✅ native n8n support
- ✅ پایدار و امن
- ✅ کار کردن با API رسمی تلگرام

### قدم‌های سریع:

#### 1. Bot بساز (3 دقیقه)
```
1. @BotFather در تلگرام
2. /newbot
3. اسم: Crypto Signal Monitor
4. username: crypto_signal_monitor_bot_2025 (اگه قبلی گرفته شد)
5. Token یادداشت کن: 123456789:ABC-DEF...
```

#### 2. به کانال‌ها اضافه کن (2 دقیقه)
```
@shervin_trading → Add Members → @crypto_signal_monitor_bot → Admin
@uniopn → Add Members → @crypto_signal_monitor_bot → Admin
```

#### 3. Workflow در n8n (5 دقیقه)
```
1. New Workflow → "Crypto Signal Monitor"
2. Add Node → "Telegram Trigger"
3. Bot Token: [TOKEN_که_یادداشت_کردی]
4. Add Node → "Code" (کد signal detection)
5. Add Node → "Telegram" (ارسال پیام)
6. Save & Test
```

### کد Signal Detection:
```javascript
const keywords = ["entry", "stop", "tp", "لوریج", "buy", "sell", "target"];
const text = items.json.message?.text || "";
const found = keywords.filter(k => text.toLowerCase().includes(k.toLowerCase()));
const confidence = Math.min(found.length * 20, 60);

if (confidence >= 40) {
  return [{
    json: {
      confidence: confidence,
      keywords: found,
      cleanText: text.replace(/https?:\/\/\S+/g, ""),
      channel: items.json.message?.chat?.title
    }
  }];
}
```

## فایل‌های آماده:
- `telegram_alternatives_guide.md` - راهنمای جامع همه راه‌حل‌ها
- `bot_api_setup_guide.md` - راهنمای کامل Bot API
- `crypto_signal_bot_api_workflow.json` - workflow آماده import

## چرا Bot API بهتر از UserBot؟

| ویژگی | Bot API | UserBot |
|-------|---------|---------|
| نصب | ساده (5 دقیقه) | پیچیده (community node) |
| پایداری | بالا | متوسط |
| امنیت | رسمی تلگرام | شخصی |
| محدودیت | فقط کانال‌های عضو | همه کانال‌ها |
| پشتیبانی | native n8n | community |

## نتیجه:
**Bot API برای نیاز تو بهتره** - سریع، پایدار و کافی برای monitoring کانال‌های @shervin_trading و @uniopn.

**می‌خوای شروع کنیم؟** 🎯