#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست نهایی پیام قیمت ارز دیجیتال - مقایسه قدیمی و جدید
"""

# Import کتابخانه‌های مورد نیاز
import sys
sys.path.append('/workspace')

# Import کلاس PublicMenuManager
from public_menu import PublicMenuManager

# تست داده نمونه
def test_crypto_message():
    """تست پیام قیمت ارزها"""
    
    # داده نمونه برای تست
    test_data = {
        'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
        'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
        'top_gainer': {'symbol': 'SOL', 'name': 'Solana', 'change_24h': 15.67, 'price_usd': 234.56},
        'top_loser': {'symbol': 'AVAX', 'name': 'Avalanche', 'change_24h': -8.45, 'price_usd': 123.45},
        'tether_irr': 113500, 'tether_change_24h': 0.12,
        'usd_irr': 113000
    }
    
    # ایجاد instance از PublicMenuManager
    manager = PublicMenuManager(None)  # db_manager را None قرار می‌دهیم چون برای تست نیاز نیست
    
    print("🧪 تست پیام قیمت ارزها - نسخه جدید")
    print("=" * 60)
    
    # فراخوانی function جدید
    result = manager.format_crypto_message(test_data)
    
    print("📱 خروجی:")
    print(result)
    print("=" * 60)
    
    # بررسی مشخصات پیام
    print(f"📏 طول پیام: {len(result)} کاراکتر")
    print(f"📝 تعداد خطوط: {len(result.split())}")
    
    # بررسی مشکلات احتمالی
    issues = []
    
    # چک کردن کاراکترهای مشکل‌ساز قدیمی
    old_format_chars = [':,.', '+.', '_', '*', '`']
    for char in old_format_chars:
        if char in result:
            issues.append(f"⚠️ کاراکتر مشکل‌ساز '{char}' هنوز موجود است")
    
    # چک کردن کاراکترهای ممنوع تلگرام
    telegram_forbidden = ['[', ']', '{', '}', '<', '>', '|', '\\', '^']
    for char in telegram_forbidden:
        if char in result:
            issues.append(f"🚫 کاراکتر ممنوع تلگرام '{char}' موجود است")
    
    if not issues:
        print("✅ هیچ مشکل کاراکتری یافت نشد!")
    else:
        print("🔍 مشکلات یافت شده:")
        for issue in issues:
            print(f"   {issue}")
    
    # چک کردن encoding
    try:
        result.encode('utf-8')
        print("✅ Encoding UTF-8 درست است")
    except UnicodeError:
        print("❌ مشکل encoding UTF-8")
    
    print("\n🎉 تست تکمیل شد!")

if __name__ == "__main__":
    test_crypto_message()
