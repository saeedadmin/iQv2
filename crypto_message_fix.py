#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
نسخه ثابت و بهینه برای فرمت پیام قیمت ارزهای دیجیتال
حل مشکل کاراکترها و encoding
"""

import re
from typing import Dict, Any

def format_crypto_message_fixed(data: Dict[str, Any]) -> str:
    """فرمت کردن پیام قیمت‌های ارز - نسخه بدون مشکل کاراکتر"""
    
    if data.get('error'):
        return f"❌ خطا در دریافت اطلاعات:\n{data['error']}"
    
    # تبدیل دلار به تومان
    usd_to_irr = data.get('usd_irr', 70000)
    if usd_to_irr == 0:
        usd_to_irr = 70000
    
    # آماده سازی متغیرهای پیام
    message_parts = []
    
    # هدر اصلی
    message_parts.append("💰 قیمتهای لحظه ای ارز")
    message_parts.append("")
    
    # بیت کوین
    btc = data.get('bitcoin', {})
    if btc.get('price_usd'):
        btc_price = int(btc['price_usd'])
        btc_irr = int(btc['price_usd'] * usd_to_irr)
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
        message_parts.append(f"💵 ${btc_price:,}")
        message_parts.append(f"💰 {btc_irr:,} تومان")
        message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
        message_parts.append("")
    
    # اتریوم
    eth = data.get('ethereum', {})
    if eth.get('price_usd'):
        eth_price = int(eth['price_usd'])
        eth_irr = int(eth['price_usd'] * usd_to_irr)
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
        message_parts.append(f"💵 ${eth_price:,}")
        message_parts.append(f"💰 {eth_irr:,} تومان")
        message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
        message_parts.append("")
    
    # بیشترین صعود
    gainer = data.get('top_gainer', {})
    if gainer.get('symbol'):
        gainer_price = gainer.get('price_usd', 0)
        gainer_irr = int(gainer_price * usd_to_irr)
        gainer_change = gainer.get('change_24h', 0)
        
        message_parts.append("🚀 بیشترین صعود:")
        message_parts.append(f"🔥 {gainer['symbol']} ({gainer.get('name', 'N/A')})")
        message_parts.append(f"💵 ${gainer_price:.4f}")
        message_parts.append(f"💰 {gainer_irr:,} تومان")
        message_parts.append(f"🔺 +{gainer_change:.2f}%")
        message_parts.append("")
    
    # بیشترین نزول
    loser = data.get('top_loser', {})
    if loser.get('symbol'):
        loser_price = loser.get('price_usd', 0)
        loser_irr = int(loser_price * usd_to_irr)
        loser_change = loser.get('change_24h', 0)
        
        message_parts.append("📉 بیشترین نزول:")
        message_parts.append(f"💥 {loser['symbol']} ({loser.get('name', 'N/A')})")
        message_parts.append(f"💵 ${loser_price:.4f}")
        message_parts.append(f"💰 {loser_irr:,} تومان")
        message_parts.append(f"🔻 {loser_change:.2f}%")
        message_parts.append("")
    
    # خط جداکننده
    message_parts.append("━━━━━━━━━━━━━━━━━━")
    message_parts.append("")
    
    # تتر
    tether_price = data.get('tether_irr', 0)
    if tether_price > 0:
        tether_change = data.get('tether_change_24h', 0)
        
        if tether_change > 0:
            change_icon = "🔺"
            change_text = f"+{tether_change:.2f}"
        elif tether_change < 0:
            change_icon = "🔻"
            change_text = f"{tether_change:.2f}"
        else:
            change_icon = "➖"
            change_text = "0.00"
        
        message_parts.append("🟢 تتر (USDT):")
        message_parts.append(f"💰 {tether_price:,} تومان")
        if tether_change != 0:
            message_parts.append(f"{change_icon} {change_text}% (24 ساعت)")
        message_parts.append("")
    else:
        message_parts.append("🟢 تتر (USDT): ❌ ناموجود")
        message_parts.append("")
    
    # دلار
    usd_price = data.get('usd_irr', 0)
    if usd_price > 0:
        message_parts.append("💵 دلار آمریکا (USD):")
        message_parts.append(f"💰 {usd_price:,} تومان")
        message_parts.append("")
    else:
        message_parts.append("💵 دلار آمریکا (USD): ❌ ناموجود")
        message_parts.append("")
    
    # فوتر
    message_parts.append("🕐 آخرین بروزرسانی: همین الان")
    message_parts.append("📊 منبع: CoinGecko, تترلند, CodeBazan")
    
    return "\n".join(message_parts)

# تست function
if __name__ == "__main__":
    # داده نمونه برای تست
    test_data = {
        'bitcoin': {'price_usd': 67543.21, 'change_24h': 2.34},
        'ethereum': {'price_usd': 3456.78, 'change_24h': -1.23},
        'top_gainer': {'symbol': 'SOL', 'name': 'Solana', 'change_24h': 15.67, 'price_usd': 234.56},
        'top_loser': {'symbol': 'AVAX', 'name': 'Avalanche', 'change_24h': -8.45, 'price_usd': 123.45},
        'tether_irr': 113500, 'tether_change_24h': 0.12,
        'usd_irr': 113000
    }
    
    print("🔧 تست پیام جدید:")
    print("=" * 50)
    result = format_crypto_message_fixed(test_data)
    print(result)
    print("=" * 50)
    print(f"📏 طول پیام: {len(result)} کاراکتر")
    print(f"📝 تعداد خطوط: {len(result.split())}")
