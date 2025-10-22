#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست API ElevenLabs برای Text-to-Speech و Speech-to-Text
"""

import os
from elevenlabs.client import ElevenLabs

# API Key
API_KEY = "sk_f7e2d6891c4aaac6bd713c239790c762e3c9556062c858f3"

client = ElevenLabs(api_key=API_KEY)

print("🔍 تست 1: بررسی اطلاعات کاربر و کردیت‌های موجود")
print("=" * 60)
try:
    # دریافت اطلاعات کاربر
    user_info = client.user.get()
    print(f"✅ نام کاربری: {user_info.subscription.character_count if hasattr(user_info, 'subscription') else 'N/A'}")
    print(f"✅ تعداد کاراکتر استفاده شده: {user_info.subscription.character_count if hasattr(user_info.subscription, 'character_count') else 'N/A'}")
    print(f"✅ محدودیت کاراکتر: {user_info.subscription.character_limit if hasattr(user_info.subscription, 'character_limit') else 'N/A'}")
    print(f"✅ کاراکتر باقی‌مانده: {user_info.subscription.character_limit - user_info.subscription.character_count if hasattr(user_info.subscription, 'character_limit') else 'N/A'}")
    print(f"\n📊 اطلاعات کامل: {user_info}")
except Exception as e:
    print(f"❌ خطا در دریافت اطلاعات کاربر: {e}")

print("\n" + "=" * 60)
print("🔍 تست 2: Text-to-Speech (انگلیسی)")
print("=" * 60)
try:
    # تست TTS انگلیسی
    text_en = "Hello! This is a test of ElevenLabs text to speech."
    print(f"📝 متن: {text_en}")
    print(f"📊 تعداد کاراکتر: {len(text_en)}")
    
    audio = client.text_to_speech.convert(
        text=text_en,
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # Voice ID پیش‌فرض
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )
    
    # ذخیره فایل صوتی
    with open("test_audio_en.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)
    
    print("✅ فایل صوتی انگلیسی با موفقیت ایجاد شد: test_audio_en.mp3")
    print(f"📁 حجم فایل: {os.path.getsize('test_audio_en.mp3') / 1024:.2f} KB")
except Exception as e:
    print(f"❌ خطا در تبدیل متن به صوت (انگلیسی): {e}")

print("\n" + "=" * 60)
print("🔍 تست 3: Text-to-Speech (فارسی)")
print("=" * 60)
try:
    # تست TTS فارسی
    text_fa = "سلام! این یک تست تبدیل متن فارسی به صوت است."
    print(f"📝 متن: {text_fa}")
    print(f"📊 تعداد کاراکتر: {len(text_fa)}")
    
    audio_fa = client.text_to_speech.convert(
        text=text_fa,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )
    
    # ذخیره فایل صوتی فارسی
    with open("test_audio_fa.mp3", "wb") as f:
        for chunk in audio_fa:
            f.write(chunk)
    
    print("✅ فایل صوتی فارسی با موفقیت ایجاد شد: test_audio_fa.mp3")
    print(f"📁 حجم فایل: {os.path.getsize('test_audio_fa.mp3') / 1024:.2f} KB")
except Exception as e:
    print(f"❌ خطا در تبدیل متن به صوت (فارسی): {e}")

print("\n" + "=" * 60)
print("🔍 تست 4: دریافت لیست صداها")
print("=" * 60)
try:
    # دریافت لیست صداهای موجود
    voices = client.voices.get_all()
    print(f"✅ تعداد صداهای موجود: {len(voices.voices)}")
    print("\n🎙️ 5 صدای اول:")
    for i, voice in enumerate(voices.voices[:5]):
        print(f"  {i+1}. {voice.name} (ID: {voice.voice_id})")
except Exception as e:
    print(f"❌ خطا در دریافت لیست صداها: {e}")

print("\n" + "="*60)
print("✅ تست‌ها تمام شد!")
print("="*60)
