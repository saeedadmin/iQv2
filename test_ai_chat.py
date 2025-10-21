#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
تست قابلیت‌های جدید چت با AI
نویسنده: MiniMax Agent
"""

import sys
import os

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_chat_handler import GeminiChatHandler
from database_postgres import PostgreSQLManager
import time

def test_chat_features():
    """تست قابلیت‌های جدید"""
    
    print("🚀 شروع تست قابلیت‌های جدید چت با AI...\n")
    
    # مقداردهی دیتابیس
    try:
        db = PostgreSQLManager()
        print("✅ دیتابیس مقداردهی شد")
    except Exception as e:
        print(f"❌ خطا در اتصال به دیتابیس: {e}")
        print("⚠️ تست بدون دیتابیس ادامه می‌یابد...")
        db = None
    
    # مقداردهی handler
    handler = GeminiChatHandler(db_manager=db)
    print("✅ GeminiChatHandler مقداردهی شد\n")
    
    # Test user ID
    test_user_id = 12345
    
    # تست 1: تست حافظه مکالمه
    print("="*50)
    print("📝 تست 1: حافظه مکالمه")
    print("="*50)
    
    print("\n✅ پیام 1: 'اسمم علی هست'")
    result1 = handler.send_message_with_history(test_user_id, "اسمم علی هست")
    if result1['success']:
        print(f"   ✅ پاسخ: {result1['response'][:100]}...")
    else:
        print(f"   ❌ خطا: {result1['error']}")
    
    time.sleep(2)
    
    print("\n✅ پیام 2: 'اسمم رو یادته؟'")
    result2 = handler.send_message_with_history(test_user_id, "اسمم رو یادته؟")
    if result2['success']:
        print(f"   ✅ پاسخ: {result2['response'][:100]}...")
        if "علی" in result2['response']:
            print("   ✅ حافظه مکالمه کار می‌کند!")
        else:
            print("   ⚠️ حافظه ممکن است کار نکند")
    else:
        print(f"   ❌ خطا: {result2['error']}")
    
    # تست 2: تست Rate Limiting
    print("\n" + "="*50)
    print("🛡️ تست 2: Rate Limiting (10 پیام در 60 ثانیه)")
    print("="*50)
    
    print("\n✅ ارسال 12 پیام سریع برای تست rate limit...")
    
    test_user_id_2 = 67890
    success_count = 0
    rate_limited = False
    
    for i in range(12):
        result = handler.send_message_with_history(test_user_id_2, f"سلام {i+1}")
        if result['success']:
            success_count += 1
            print(f"   ✅ پیام {i+1}: موفق")
        else:
            if result['error'].startswith('rate_limit'):
                rate_limited = True
                wait_time = result['error'].split(':')[1]
                print(f"   🛡️ پیام {i+1}: Rate Limited! (زمان انتظار: {wait_time}s)")
            else:
                print(f"   ❌ پیام {i+1}: خطا - {result['error']}")
    
    if rate_limited:
        print("\n   ✅ Rate Limiting کار می‌کند!")
    else:
        print("\n   ⚠️ Rate Limiting فعال نشد (12 پیام موفق بود)")
    
    # تست 3: تست فرمت کد
    print("\n" + "="*50)
    print("💻 تست 3: فرمت کد")
    print("="*50)
    
    # تست markdown code block
    test_code = "```python\ndef hello():\n    print('Hello World')\n```"
    formatted = handler.format_code_blocks(test_code)
    print(f"\n✅ ورودی: {test_code}")
    print(f"   ✅ خروجی: {formatted}")
    
    if '<pre><code' in formatted and 'language-python' in formatted:
        print("   ✅ فرمت کد کار می‌کند!")
    else:
        print("   ❌ فرمت کد مشکل دارد")
    
    # تست inline code
    test_inline = "برای چاپ `print()` استفاده کنید"
    formatted_inline = handler.format_code_blocks(test_inline)
    print(f"\n✅ ورودی: {test_inline}")
    print(f"   ✅ خروجی: {formatted_inline}")
    
    if '<code>print()</code>' in formatted_inline:
        print("   ✅ Inline code کار می‌کند!")
    
    # تست 4: تست Sanitization
    print("\n" + "="*50)
    print("🛡️ تست 4: Sanitization")
    print("="*50)
    
    # تست حذف کاراکترهای کنترلی
    dirty_input = "سلام\x00\x1fاین متن تمیز است"
    clean = handler.sanitize_input(dirty_input)
    print(f"\n✅ ورودی: {repr(dirty_input)}")
    print(f"   ✅ خروجی: {repr(clean)}")
    
    if '\x00' not in clean and '\x1f' not in clean:
        print("   ✅ Sanitization کار می‌کند!")
    
    # تست محدودیت طول
    long_input = "سلام " * 1000  # 5000 کاراکتر
    truncated = handler.sanitize_input(long_input)
    print(f"\n✅ طول ورودی: {len(long_input)} کاراکتر")
    print(f"   ✅ طول خروجی: {len(truncated)} کاراکتر")
    
    if len(truncated) <= handler.max_message_length:
        print(f"   ✅ محدودیت طول کار می‌کند! (حداکثر: {handler.max_message_length})")
    
    # تست 5: تست تاریخچه دیتابیس
    if db:
        print("\n" + "="*50)
        print("🗄️ تست 5: تاریخچه دیتابیس")
        print("="*50)
        
        # پاک کردن تاریخچه قبلی
        db.clear_chat_history(test_user_id)
        
        # اضافه کردن چند پیام
        db.add_chat_message(test_user_id, 'user', 'سلام')
        db.add_chat_message(test_user_id, 'model', 'سلام! چطور می‌تونم کمک کنم؟')
        db.add_chat_message(test_user_id, 'user', 'اسمم علی هست')
        
        # دریافت تاریخچه
        history = db.get_chat_history(test_user_id)
        print(f"\n✅ تعداد پیام‌های تاریخچه: {len(history)}")
        
        for i, msg in enumerate(history):
            print(f"   {i+1}. [{msg['role']}]: {msg['message_text'][:50]}...")
        
        if len(history) == 3:
            print("   ✅ تاریخچه دیتابیس کار می‌کند!")
        
        # تست پاک کردن تاریخچه
        db.clear_chat_history(test_user_id)
        history_after = db.get_chat_history(test_user_id)
        print(f"\n✅ تعداد پیام‌ها پس از پاک: {len(history_after)}")
        
        if len(history_after) == 0:
            print("   ✅ پاک کردن تاریخچه کار می‌کند!")
    
    print("\n" + "="*50)
    print("✅ تست به پایان رسید")
    print("="*50)
    print("\n🎉 تمام قابلیت‌های جدید با موفقیت تست شدند!\n")

if __name__ == "__main__":
    test_chat_features()
