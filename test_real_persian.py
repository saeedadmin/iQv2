#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست واقعی OCR با متن فارسی مختلف
"""

import io
from PIL import Image, ImageDraw, ImageFont
import sys
import os

sys.path.append('/workspace')
from ocr_handler import OCRHandler

def create_various_persian_texts():
    """ایجاد تصاویر با متن‌های مختلف فارسی"""
    
    test_cases = [
        {
            'title': 'متن ساده فارسی',
            'text': 'این یک متن فارسی ساده است'
        },
        {
            'title': 'متن فارسی و انگلیسی',
            'text': 'Hello World - سلام دنیا'
        },
        {
            'title': 'اعداد و متن فارسی',
            'text': 'عدد ۱۲۳ و متن فارسی تست'
        },
        {
            'title': 'متن طولانی فارسی',
            'text': 'این یک متن طولانی‌تر فارسی است که برای تست کیفیت OCR استفاده می‌شود'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        # ایجاد تصویر
        image = Image.new('RGB', (600, 200), color='white')
        draw = ImageDraw.Draw(image)
        
        # انتخاب فونت
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except:
            font = ImageFont.load_default()
        
        # کشیدن عنوان
        draw.text((20, 20), test_case['title'], fill='black', font=font)
        
        # کشیدن متن اصلی
        draw.text((20, 70), test_case['text'], fill='black', font=font)
        
        # ذخیره تصویر
        image_path = f'/workspace/test_case_{i+1}.png'
        image.save(image_path)
        
        # تبدیل به bytes
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_data = image_bytes.getvalue()
        
        # تست OCR
        ocr_handler = OCRHandler()
        result = ocr_handler.extract_text_from_image(image_data, test_case['title'])
        
        results.append({
            'test_case': test_case,
            'image_path': image_path,
            'ocr_result': result
        })
    
    return results

def main():
    """تست اصلی"""
    print("🇮🇷 تست کامل OCR فارسی")
    print("=" * 60)
    
    results = create_various_persian_texts()
    
    total_success = 0
    total_chars = 0
    
    for i, result in enumerate(results, 1):
        print(f"\n📋 تست {i}: {result['test_case']['title']}")
        print("-" * 40)
        
        if result['ocr_result'].get('success'):
            total_success += 1
            extracted = result['ocr_result']['extracted_text']
            total_chars += len(extracted)
            
            print(f"✅ موفق")
            print(f"📝 متن اصلی: '{result['test_case']['text']}'")
            print(f"📝 متن استخراج شده: '{extracted}'")
            print(f"🔢 کاراکتر: {len(extracted)}")
            print(f"📊 کیفیت: {result['ocr_result'].get('confidence', 0)*100:.1f}%")
            print(f"⏱️ زمان: {result['ocr_result'].get('processing_time', 0):.2f}s")
        else:
            print(f"❌ خطا: {result['ocr_result'].get('error', 'نامشخص')}")
    
    # خلاصه کلی
    print(f"\n🎯 خلاصه کلی:")
    print("=" * 30)
    print(f"✅ موفقیت: {total_success}/{len(results)}")
    print(f"📊 نرخ موفقیت: {total_success/len(results)*100:.1f}%")
    print(f"📝 مجموع کاراکتر استخراج شده: {total_chars}")
    
    if total_success == len(results):
        print("🎉 همه تست‌ها موفق بودند!")
    elif total_success > 0:
        print("⚠️ برخی تست‌ها موفق بودند")
    else:
        print("❌ هیچ تستی موفق نبود")

if __name__ == "__main__":
    main()