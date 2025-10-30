#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Crypto Service
سرویس مربوط به ارزهای دیجیتال و شاخص ترس و طمع
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def fetch_fear_greed_index():
    """دریافت شاخص ترس و طمع بازار کریپتو از alternative.me"""
    import aiohttp
    import json
    
    try:
        url = "https://api.alternative.me/fng/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and 'data' in data and len(data['data']) > 0:
                        fng_data = data['data'][0]
                        value = int(fng_data.get('value', 50))
                        classification = fng_data.get('value_classification', 'Unknown')
                        
                        # تعیین حالت فارسی و ایموجی
                        if value <= 25:
                            mood_fa = 'ترس شدید'
                            emoji = '😱'
                            color = '🔴'
                        elif value <= 45:
                            mood_fa = 'ترس'
                            emoji = '😰'
                            color = '🟠'
                        elif value <= 55:
                            mood_fa = 'خنثی'
                            emoji = '😐'
                            color = '🟡'
                        elif value <= 75:
                            mood_fa = 'طمع'
                            emoji = '😃'
                            color = '🟢'
                        else:
                            mood_fa = 'طمع شدید'
                            emoji = '🤑'
                            color = '🟢'
                        
                        # زمان آپدیت
                        timestamp = int(fng_data.get('timestamp', 0))
                        if timestamp:
                            update_time = datetime.fromtimestamp(timestamp)
                        else:
                            update_time = datetime.now()
                        
                        return {
                            'value': value,
                            'classification': classification,
                            'mood_fa': mood_fa,
                            'emoji': emoji,
                            'color': color,
                            'update_time': update_time,
                            'success': True
                        }
                    else:
                        raise Exception("Invalid API response format")
                else:
                    raise Exception(f"API request failed with status {response.status}")
                    
    except Exception as e:
        logger.error(f"خطا در دریافت شاخص ترس و طمع: {e}")
        return {
            'value': 50,
            'classification': 'Neutral',
            'mood_fa': 'خنثی',
            'emoji': '😐',
            'color': '🟡',
            'update_time': datetime.now(),
            'success': False,
            'error': str(e)
        }


async def download_fear_greed_chart():
    """دانلود تصویر چارت شاخص ترس و طمع از منابع مختلف"""
    import aiohttp
    import os
    import tempfile
    
    # لیست منابع مختلف برای تصویر
    image_sources = [
        "https://alternative.me/crypto/fear-and-greed-index.png",
        "https://alternative.me/images/fng/crypto-fear-and-greed-index.png", 
        "https://api.alternative.me/fng/png"
    ]
    
    # استفاده از پوشه موقت سیستم برای جلوگیری از مشکلات مجوز
    temp_dir = tempfile.gettempdir()
    chart_path = os.path.join(temp_dir, "fear_greed_chart.png")
    
    # Headers برای شبیه‌سازی درخواست مرورگر
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'image/png,image/webp,image/jpeg,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    
    for i, chart_url in enumerate(image_sources, 1):
        try:
            logger.info(f"تلاش {i}: دانلود از {chart_url}")
            
            async with aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(chart_url) as response:
                    logger.info(f"وضعیت پاسخ: {response.status}")
                    
                    if response.status == 200:
                        content = await response.read()
                        logger.info(f"حجم محتوا: {len(content)} بایت")
                        
                        # بررسی اینکه محتوا یک تصویر واقعی است
                        if len(content) > 1000:  # حداقل 1KB برای تصویر
                            # بررسی magic bytes برای PNG
                            if content.startswith(b'\x89PNG') or content.startswith(b'\xff\xd8\xff'):
                                with open(chart_path, 'wb') as f:
                                    f.write(content)
                                
                                if os.path.exists(chart_path) and os.path.getsize(chart_path) > 1000:
                                    logger.info(f"✅ تصویر با موفقیت دانلود شد: {chart_path}")
                                    return chart_path
                                else:
                                    logger.warning("❌ مشکل در ذخیره فایل")
                            else:
                                logger.warning("❌ محتوا تصویر معتبری نیست")
                        else:
                            logger.warning(f"❌ حجم محتوا خیلی کم است: {len(content)} بایت")
                    else:
                        logger.warning(f"❌ کد خطای HTTP: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ خطا در منبع {i}: {e}")
            continue
    
    logger.warning("❌ هیچ منبعی کار نکرد - ایجاد تصویر ساده...")
    return await create_simple_fear_greed_image()


async def create_simple_fear_greed_image():
    """ایجاد تصویر ساده شاخص ترس و طمع"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import math
        import os
        
        # دریافت مقدار فعلی شاخص
        index_data = await fetch_fear_greed_index()
        value = index_data.get('value', 50)
        
        # ایجاد canvas
        width, height = 400, 300
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # رنگ براساس مقدار
        if value <= 25:
            color = '#FF0000'  # قرمز - ترس شدید
        elif value <= 45:
            color = '#FF8000'  # نارنجی - ترس
        elif value <= 55:
            color = '#FFFF00'  # زرد - خنثی
        elif value <= 75:
            color = '#80FF00'  # سبز روشن - طمع
        else:
            color = '#00FF00'  # سبز - طمع شدید
        
        # رسم دایره اصلی
        center_x, center_y = width // 2, height // 2 + 20
        radius = 100
        
        # رسم قوس نیم دایره
        for angle in range(180):
            end_x = center_x + radius * math.cos(math.radians(180 - angle))
            end_y = center_y - radius * math.sin(math.radians(180 - angle))
            
            # رنگ گرادیانت
            progress = angle / 180
            if progress < 0.25:
                arc_color = '#FF0000'
            elif progress < 0.45:
                arc_color = '#FF8000'
            elif progress < 0.55:
                arc_color = '#FFFF00'
            elif progress < 0.75:
                arc_color = '#80FF00'
            else:
                arc_color = '#00FF00'
            
            draw.line([(center_x, center_y), (end_x, end_y)], fill=arc_color, width=3)
        
        # رسم عقربه
        needle_angle = 180 - (value * 180 / 100)
        needle_x = center_x + (radius - 10) * math.cos(math.radians(needle_angle))
        needle_y = center_y - (radius - 10) * math.sin(math.radians(needle_angle))
        draw.line([(center_x, center_y), (needle_x, needle_y)], fill='black', width=5)
        
        # نوشتن متن
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # نوشتن مقدار
        text = f"{value}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((center_x - text_width//2, center_y + 30), text, fill='black', font=font)
        
        # نوشتن برچسب‌ها
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            small_font = ImageFont.load_default()
        
        draw.text((30, center_y + 10), "Fear", fill='red', font=small_font)
        draw.text((width - 70, center_y + 10), "Greed", fill='green', font=small_font)
        
        # ذخیره فایل در پوشه موقت سیستم
        import tempfile
        temp_dir = tempfile.gettempdir()
        chart_path = os.path.join(temp_dir, "fear_greed_chart.png")
        img.save(chart_path, 'PNG')
        
        if os.path.exists(chart_path):
            logger.info(f"✅ تصویر ساده ایجاد شد: {chart_path}")
            return chart_path
        else:
            logger.error("❌ مشکل در ایجاد تصویر ساده")
            return None
            
    except Exception as e:
        logger.error(f"❌ خطا در ایجاد تصویر ساده: {e}")
        return None


def format_fear_greed_message(index_data):
    """فرمت کردن پیام شاخص ترس و طمع"""
    
    if not index_data['success']:
        return f"""😨 شاخص ترس و طمع بازار کریپتو

❌ متاسفانه در حال حاضر امکان دریافت اطلاعات وجود ندارد.

🔄 لطفاً چند دقیقه بعد دوباره تلاش کنید.

📊 منبع: Alternative.me Fear & Greed Index"""

    value = index_data['value']
    classification = index_data['classification']
    mood_fa = index_data['mood_fa']
    emoji = index_data['emoji']
    color = index_data['color']
    update_time = index_data['update_time']
    
    # توضیحات
    if value <= 25:
        description = "بازار در حالت ترس شدید است. سرمایه‌گذاران نگران هستند و احتمال فروش بالاست."
    elif value <= 45:
        description = "بازار در حالت ترس است. احتیاط در تصمیم‌گیری توصیه می‌شود."
    elif value <= 55:
        description = "بازار در حالت خنثی است. هیچ احساس خاصی در بازار حاکم نیست."
    elif value <= 75:
        description = "بازار در حالت طمع است. سرمایه‌گذاران خوش‌بین هستند."
    else:
        description = "بازار در حالت طمع شدید است. احتمال اصلاح قیمت وجود دارد."

    message = f"""😨 شاخص ترس و طمع بازار کریپتو

{color} **مقدار فعلی:** {value}/100
{emoji} **وضعیت:** {mood_fa} ({classification})

📝 **توضیحات:**
{description}

🕐 **زمان آپدیت:** {update_time.strftime('%Y/%m/%d - %H:%M')}

💡 **نکته:** این شاخص بر اساس تحلیل احساسات بازار، حجم معاملات، نوسانات و ... محاسبه می‌شود.

📊 منبع: Alternative.me Fear & Greed Index

⚠️ توجه: این شاخص صرفاً جهت اطلاع‌رسانی است و توصیه سرمایه‌گذاری نمی‌باشد."""

    return message
