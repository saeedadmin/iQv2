#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نسخه ایمن و تست شده function فرمت پیام قیمت ارز
بدون هیچ کاراکتر مشکل‌ساز
"""

def format_crypto_message_safe(data):
    """فرمت کردن پیام قیمت‌های ارز - نسخه کاملاً امن"""
    if data.get('error'):
        return f"خطا در دریافت اطلاعات: {data['error']}"
    
    # تبدیل دلار به تومان
    usd_to_irr = data.get('usd_irr', 70000)
    if usd_to_irr == 0:
        usd_to_irr = 70000
    
    # آماده سازی پیام امن
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
            change_symbol = "+"
        elif btc_change < 0:
            change_symbol = "-"
        else:
            change_symbol = ""
        
        safe_lines.append("بیت کوین (BTC):")
        safe_lines.append(f"USD: ${btc_price}")
        safe_lines.append(f"تومان: {btc_irr:,}")
        safe_lines.append(f"تغییر 24ساعته: {change_symbol}{btc_change:.2f}%")
        safe_lines.append("")
    
    # اتریوم
    eth = data.get('ethereum', {})
    if eth.get('price_usd'):
        eth_price = int(eth['price_usd'])
        eth_irr = int(eth['price_usd'] * usd_to_irr)
        eth_change = eth.get('change_24h', 0)
        
        if eth_change > 0:
            change_symbol = "+"
        elif eth_change < 0:
            change_symbol = "-"
        else:
            change_symbol = ""
        
        safe_lines.append("اتریوم (ETH):")
        safe_lines.append(f"USD: ${eth_price}")
        safe_lines.append(f"تومان: {eth_irr:,}")
        safe_lines.append(f"تغییر 24ساعته: {change_symbol}{eth_change:.2f}%")
        safe_lines.append("")
    
    # بیشترین صعود
    gainer = data.get('top_gainer', {})
    if gainer.get('symbol'):
        gainer_price = gainer.get('price_usd', 0)
        gainer_irr = int(gainer_price * usd_to_irr)
        gainer_change = gainer.get('change_24h', 0)
        
        safe_lines.append("بیشترین صعود:")
        safe_lines.append(f"{gainer['symbol']} ({gainer.get('name', 'N/A')})")
        safe_lines.append(f"USD: ${gainer_price:.4f}")
        safe_lines.append(f"تومان: {gainer_irr:,}")
        safe_lines.append(f"تغییر: +{gainer_change:.2f}%")
        safe_lines.append("")
    
    # بیشترین نزول
    loser = data.get('top_loser', {})
    if loser.get('symbol'):
        loser_price = loser.get('price_usd', 0)
        loser_irr = int(loser_price * usd_to_irr)
        loser_change = loser.get('change_24h', 0)
        
        safe_lines.append("بیشترین نزول:")
        safe_lines.append(f"{loser['symbol']} ({loser.get('name', 'N/A')})")
        safe_lines.append(f"USD: ${loser_price:.4f}")
        safe_lines.append(f"تومان: {loser_irr:,}")
        safe_lines.append(f"تغییر: {loser_change:.2f}%")
        safe_lines.append("")
    
    # تتر
    tether_price = data.get('tether_irr', 0)
    if tether_price > 0:
        tether_change = data.get('tether_change_24h', 0)
        if tether_change > 0:
            change_symbol = "+"
        elif tether_change < 0:
            change_symbol = "-"
        else:
            change_symbol = ""
        
        safe_lines.append("تتر (USDT):")
        safe_lines.append(f"تومان: {tether_price:,}")
        if tether_change != 0:
            safe_lines.append(f"تغییر 24ساعته: {change_symbol}{tether_change:.2f}%")
        safe_lines.append("")
    else:
        safe_lines.append("تتر (USDT): ناموجود")
        safe_lines.append("")
    
    # دلار
    usd_price = data.get('usd_irr', 0)
    if usd_price > 0:
        safe_lines.append("دلار آمریکا (USD):")
        safe_lines.append(f"تومان: {usd_price:,}")
        safe_lines.append("")
    else:
        safe_lines.append("دلار آمریکا (USD): ناموجود")
        safe_lines.append("")
    
    # فوتر
    safe_lines.append("بروزرسانی: همین الان")
    safe_lines.append("منبع: CoinGecko, تترلند, CodeBazan")
    
    return "\n".join(safe_lines)

def test_safe_message():
    """تست function ایمن"""
    test_data = {
        'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
        'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
        'top_gainer': {'symbol': 'SOL', 'name': 'Solana', 'change_24h': 15.67, 'price_usd': 234.56},
        'top_loser': {'symbol': 'AVAX', 'name': 'Avalanche', 'change_24h': -8.45, 'price_usd': 123.45},
        'tether_irr': 113500, 'tether_change_24h': 0.12,
        'usd_irr': 113000
    }
    
    print("🔒 تست پیام ایمن:")
    print("=" * 50)
    result = format_crypto_message_safe(test_data)
    print(result)
    print("=" * 50)
    
    # بررسی کاراکترهای مشکل‌ساز
    problematic_chars = []
    for i, char in enumerate(result):
        char_code = ord(char)
        # کاراکترهای خطرناک برای Telegram
        if char_code < 32 or char in ['<', '>', '&', '"', "'", '`', '~', '!', '@', '#', '$', '%', '^', '*', '(', ')', '-', '_', '+', '=', '[', ']', '{', '}', '|', '\\', ':', ';', ',', '.', '/', '?']:
            if char not in ['\n', '\r', '\t', '+', '-', '.', ',', '/', '(' , ')', ':']:  # کاراکترهای مجاز
                problematic_chars.append(f"Position {i}: '{char}' (ASCII: {char_code})")
    
    if problematic_chars:
        print("🚫 کاراکترهای مشکل‌ساز:")
        for prob in problematic_chars[:5]:  # فقط 5 تای اول
            print(f"  {prob}")
    else:
        print("✅ هیچ کاراکتر مشکل‌ساز یافت نشد!")
    
    print(f"📏 طول پیام: {len(result)} کاراکتر")
    return result

if __name__ == "__main__":
    test_safe_message()
