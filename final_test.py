#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تست نهایی function جدید فرمت پیام قیمت ارز
"""

def format_crypto_message(data):
    """فرمت کردن پیام قیمت‌های ارز - نسخه فوق‌العاده امن"""
    if data.get('error'):
        return f"خطا در دریافت اطلاعات: {data['error']}"
    
    # تبدیل دلار به تومان
    usd_to_irr = data.get('usd_irr', 70000)
    if usd_to_irr == 0:
        usd_to_irr = 70000
    
    # آماده سازی پیام ایمن
    safe_lines = []
    
    # هدر ساده
    safe_lines.append("قیمتهای لحظه ای ارز")
    safe_lines.append("")
    
    # بیت کوین
    btc = data.get('bitcoin', {})
    if btc.get('price_usd'):
        btc_price = int(btc['price_usd'])
        btc_irr = int(btc['price_usd'] * usd_to_irr)
        btc_change = btc.get('change_24h', 0)
        
        if btc_change > 0:
            change_text = "صعود"
        elif btc_change < 0:
            change_text = "نزول"
        else:
            change_text = "بدون تغییر"
        
        safe_lines.append("بیت کوین (BTC):")
        safe_lines.append(f"قیمت: {btc_price} دلار")
        safe_lines.append(f"تومان: {btc_irr:,}")
        safe_lines.append(f"وضعیت 24ساعته: {change_text} {abs(btc_change):.2f} درصد")
        safe_lines.append("")
    
    # اتریوم
    eth = data.get('ethereum', {})
    if eth.get('price_usd'):
        eth_price = int(eth['price_usd'])
        eth_irr = int(eth['price_usd'] * usd_to_irr)
        eth_change = eth.get('change_24h', 0)
        
        if eth_change > 0:
            change_text = "صعود"
        elif eth_change < 0:
            change_text = "نزول"
        else:
            change_text = "بدون تغییر"
        
        safe_lines.append("اتریوم (ETH):")
        safe_lines.append(f"قیمت: {eth_price} دلار")
        safe_lines.append(f"تومان: {eth_irr:,}")
        safe_lines.append(f"وضعیت 24ساعته: {change_text} {abs(eth_change):.2f} درصد")
        safe_lines.append("")
    
    # فوتر
    safe_lines.append("بروزرسانی: همین الان")
    safe_lines.append("منبع: CoinGecko, تترلند, CodeBazan")
    
    return "\n".join(safe_lines)

# تست
test_data = {
    'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
    'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
    'tether_irr': 113500, 'tether_change_24h': 0.12,
    'usd_irr': 113000
}

print("🔧 تست نهایی function جدید:")
print("=" * 50)
result = format_crypto_message(test_data)
print(result)
print("=" * 50)

# بررسی کاراکترهای ممنوع
forbidden = ['$', '%', '&', '"', "'", '<', '>', '`', '~']
found_forbidden = [c for c in forbidden if c in result]

if found_forbidden:
    print(f"❌ کاراکترهای ممنوع یافت شد: {found_forbidden}")
else:
    print("✅ هیچ کاراکتر ممنوع یافت نشد!")

print(f"📏 طول پیام: {len(result)} کاراکتر")
print("✅ Function جدید آماده استفاده!")
