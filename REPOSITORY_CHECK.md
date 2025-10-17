# Repository Structure Check

## فایل‌های ضروری که باید در ریشه repository موجود باشند:

✅ Procfile
✅ requirements.txt  
✅ runtime.txt
✅ telegram_bot.py
✅ Dockerfile (اختیاری)

## بررسی فایل‌ها:

### 1. Procfile محتوا:
```
web: python telegram_bot.py
worker: python telegram_bot.py
```

### 2. requirements.txt شامل:
```
python-telegram-bot>=22.5
psutil>=5.9.0
aiohttp>=3.8.0
python-dotenv>=1.0.0
requests>=2.28.0
beautifulsoup4>=4.12.0
playwright>=1.40.0
lxml>=4.9.0
feedparser>=6.0.10
Pillow>=10.0.0
apify-client>=2.2.0
```

### 3. runtime.txt:
```
python-3.12.5
```

## مراحل debugging:

1. در GitHub repository، branch main یا master را بررسی کن
2. مطمئن شو همه فایل‌ها در ریشه (root) هستند
3. آخرین commit را بررسی کن که همه فایل‌ها موجود باشند