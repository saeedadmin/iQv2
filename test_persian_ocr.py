#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست OCR برای متن فارسی
"""

import io
from PIL import Image, ImageDraw, ImageFont
import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append('/workspace')
from ocr_handler import OCRHandler

def create_persian_test_image():
    """ایجاد تصویر تست با متن فارسی"""
    
    # ایجاد تصویر جدید
    image = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(image)
    
    # متن‌های تست فارسی
    persian_texts = [
        "این یک متن تست فارسی است",
        "Hello World - متن انگلیسی",
        "تشخیص متن فارسی و انگلیسی",
        "OCR Persian & English Test"
    ]
    
    # انتخاب فونت (اگر موجود نباشد از پیش‌فرض استفاده می‌کند)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    except:
        font = ImageFont.load_default()
    
    # کشیدن متن‌ها
    y_position = 50
    for text in persian_texts:
        draw.text((50, y_position), text, fill='black', font=font)
        y_position += 70
    
    return image

def test_persian_ocr():
    """تست OCR فارسی"""
    
    print("🇮🇷 تست OCR برای متن فارسی")
    print("=" * 50)
    
    # ایجاد تصویر تست
    test_image = create_persian_test_image()
    
    # ذخیره تصویر برای بررسی
    test_image.save('/workspace/test_persian_image.png')
    print("📸 تصویر تست ایجاد شد: test_persian_image.png")
    
    # تبدیل به bytes
    image_bytes = io.BytesIO()
    test_image.save(image_bytes, format='PNG')
    image_data = image_bytes.getvalue()
    
    # ایجاد OCR handler
    ocr_handler = OCRHandler()
    
    # تست OCR
    print("\n🔍 شروع تست OCR...")
    result = ocr_handler.extract_text_from_image(image_data, "تست متن فارسی و انگلیسی")
    
    # نمایش نتایج
    print("\n📋 نتایج تست:")
    print("-" * 30)
    
    if result.get('success'):
        print(f"✅ موفقیت آمیز")
        print(f"📝 متن استخراج شده:")
        print(f"'{result['extracted_text']}'")
        print(f"🔢 تعداد کاراکتر: {len(result['extracted_text'])}")
        print(f"📊 کیفیت: {result.get('confidence', 0)*100:.1f}%")
        print(f"⏱️ زمان پردازش: {result.get('processing_time', 0):.2f} ثانیه")
        print(f"🔧 روش: {result.get('method', 'unknown')}")
        print(f"🌐 زبان‌ها: {result.get('languages', 'unknown')}")
    else:
        print(f"❌ خطا: {result.get('error', 'خطای نامشخص')}")
        if 'method' in result:
            print(f"🔧 روش: {result['method']}")
    
    return result

if __name__ == "__main__":
    test_persian_ocr()