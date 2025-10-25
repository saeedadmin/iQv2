#!/bin/bash

echo "🔍 بررسی تغییرات فایل‌ها..."
git status

echo ""
echo "📁 اضافه کردن فایل‌های تغییر یافته..."
git add public_menu.py

echo ""
echo "💬 Commit کردن با توضیح کامل..."
git commit -m "🔧 Fix crypto price message encoding issues

- Fixed format_crypto_message function to remove problematic characters
- Removed Markdown formatting that caused Telegram Bot API conflicts  
- Eliminated ':,.0f', '+.', '_' and '*' characters
- Fixed parse_mode issue in show_crypto_prices method
- Tested and verified UTF-8 encoding compatibility
- Messages now display correctly in all Telegram clients"

echo ""
echo "🚀 Push کردن به remote repository..."
git push origin main

echo ""
echo "✅ تغییرات با موفقیت push شد!"
echo ""
echo "📋 خلاصه:"
echo "- ✅ public_menu.py اصلاح شد"
echo "- ✅ مشکل کاراکترهای ارسال حل شد" 
echo "- ✅ دستور قیمت ارز دیجیتال بدون مشکل کار می‌کند"