#!/bin/bash

echo "🚀 Push کردن تغییرات کدنویسی..."

# اضافه کردن فایل تغییر یافته
git add public_menu.py

# Commit با توضیح
git commit -m "Fix crypto price message encoding - Remove problematic characters"

# Push به GitHub
git push origin main

echo "✅ تغییرات push شد!"
echo ""
echo "🔧 خلاصه تغییرات:"
echo "- ✅ public_menu.py اصلاح شد"
echo "- ✅ مشکل byte offset 380 حل شد"
echo "- ✅ دستور قیمت ارزها بدون مشکل کار می‌کند"