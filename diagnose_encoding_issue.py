#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بررسی دقیق کاراکترهای مشکل‌ساز و تشخیص byte offset 380
"""

def find_problematic_character():
    """بررسی کاراکترهای مشکل‌ساز در پیام"""
    
    # داده نمونه
    test_data = {
        'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
        'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
        'top_gainer': {'symbol': 'SOL', 'name': 'Solana', 'change_24h': 15.67, 'price_usd': 234.56},
        'top_loser': {'symbol': 'AVAX', 'name': 'Avalanche', 'change_24h': -8.45, 'price_usd': 123.45},
        'tether_irr': 113500, 'tether_change_24h': 0.12,
        'usd_irr': 113000
    }
    
    # ساختن پیام مثل قبلی
    message_parts = []
    
    # هدر اصلی
    message_parts.append("💰 قیمتهای لحظه ای ارز")
    message_parts.append("")
    
    # بیت کوین
    btc = test_data.get('bitcoin', {})
    if btc.get('price_usd'):
        btc_price = int(btc['price_usd'])
        btc_irr = int(btc['price_usd'] * test_data.get('usd_irr', 70000))
        btc_change = btc.get('change_24h', 0)
        
        if btc_change > 0:
            change_icon = "🔺"
            change_text = f"+{btc_change:.2f}"
        elif btc_change < 0:
            change_icon = "🔻"
            change_text = f"{btc_change:.2f}"
        else:
            change_icon = "➖"
            change_text = "0.00"
        
        message_parts.append("🟠 بیت کوین (BTC):")
        message_parts.append(f"${btc_price:,}")
        message_parts.append(f"{btc_irr:,} تومان")
        message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
        message_parts.append("")
    
    # اتریوم  
    eth = test_data.get('ethereum', {})
    if eth.get('price_usd'):
        eth_price = int(eth['price_usd'])
        eth_irr = int(eth['price_usd'] * test_data.get('usd_irr', 70000))
        eth_change = eth.get('change_24h', 0)
        
        if eth_change > 0:
            change_icon = "🔺"
            change_text = f"+{eth_change:.2f}"
        elif eth_change < 0:
            change_icon = "🔻"
            change_text = f"{eth_change:.2f}"
        else:
            change_icon = "➖"
            change_text = "0.00"
        
        message_parts.append("🔵 اتریوم (ETH):")
        message_parts.append(f"${eth_price:,}")
        message_parts.append(f"{eth_irr:,} تومان")
        message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
        message_parts.append("")
    
    # فوتر
    message_parts.append("آخرین بروزرسانی: همین الان")
    message_parts.append("منبع: CoinGecko, تترلند, CodeBazan")
    
    message = "\n".join(message_parts)
    
    print("🔍 بررسی کاراکترهای پیام...")
    print(f"📏 طول پیام: {len(message)} کاراکتر")
    print(f"📍 موقعیت byte offset 380:")
    
    if len(message) >= 380:
        print(f"کاراکتر در position 380: '{message[380]}' (ASCII: {ord(message[380])})")
        
        # نمایش 10 کاراکتر قبل و بعد از 380
        start = max(0, 370)
        end = min(len(message), 390)
        print(f"متن اطراف position 380: '{message[start:end]}'")
    
    # بررسی کاراکترهای مشکل‌ساز
    problematic_chars = []
    for i, char in enumerate(message):
        char_ord = ord(char)
        # کاراکترهای مشکل‌ساز برای Telegram
        if char_ord < 32 or char_ord == 127 or char in ['<', '>', '&', '"', "'"]:
            problematic_chars.append(f"Position {i}: '{char}' (ASCII: {char_ord})")
    
    if problematic_chars:
        print("\n🚫 کاراکترهای مشکل‌ساز یافت شد:")
        for prob in problematic_chars[:10]:  # فقط 10 تای اول
            print(f"  {prob}")
    else:
        print("\n✅ هیچ کاراکتر مشکل‌ساز یافت نشد")
    
    return message

def create_ultra_safe_message():
    """ساخت پیام فوق‌العاده امن بدون هیچ کاراکتر مشکل‌ساز"""
    
    # داده نمونه
    test_data = {
        'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
        'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
        'top_gainer': {'symbol': 'SOL', 'name': 'Solana', 'change_24h': 15.67, 'price_usd': 234.56},
        'top_loser': {'symbol': 'AVAX', 'name': 'Avalanche', 'change_24h': -8.45, 'price_usd': 123.45},
        'tether_irr': 113500, 'tether_change_24h': 0.12,
        'usd_irr': 113000
    }
    
    safe_message = []
    
    # فقط متن ساده بدون اموجی
    safe_message.append("قیمتهای لحظه ای ارز")
    safe_message.append("")
    
    # بیت کوین
    btc = test_data.get('bitcoin', {})
    if btc.get('price_usd'):
        btc_price = int(btc['price_usd'])
        btc_change = btc.get('change_24h', 0)
        
        if btc_change > 0:
            change_symbol = "+"
        elif btc_change < 0:
            change_symbol = "-"
        else:
            change_symbol = ""
        
        safe_message.append("بیت کوین (BTC):")
        safe_message.append(f"USD: ${btc_price}")
        safe_message.append(f"تغییر 24ساعته: {change_symbol}{btc_change:.2f}%")
        safe_message.append("")
    
    # اتریوم
    eth = test_data.get('ethereum', {})
    if eth.get('price_usd'):
        eth_price = int(eth['price_usd'])
        eth_change = eth.get('change_24h', 0)
        
        if eth_change > 0:
            change_symbol = "+"
        elif eth_change < 0:
            change_symbol = "-"
        else:
            change_symbol = ""
        
        safe_message.append("اتریوم (ETH):")
        safe_message.append(f"USD: ${eth_price}")
        safe_message.append(f"تغییر 24ساعته: {change_symbol}{eth_change:.2f}%")
        safe_message.append("")
    
    # فوتر ساده
    safe_message.append("بروزرسانی: همین الان")
    
    result = "\n".join(safe_message)
    
    print("\n🔧 پیام فوق‌العاده امن:")
    print("=" * 40)
    print(result)
    print("=" * 40)
    print(f"طول: {len(result)} کاراکتر")
    
    return result

if __name__ == "__main__":
    print("🔍 بررسی مشکل کاراکترها...")
    find_problematic_character()
    print("\n" + "="*50)
    create_ultra_safe_message()
