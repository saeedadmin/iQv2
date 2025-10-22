#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تست Speech-to-Text API ElevenLabs
"""

import os
from elevenlabs.client import ElevenLabs

# API Key
API_KEY = "sk_f7e2d6891c4aaac6bd713c239790c762e3c9556062c858f3"

client = ElevenLabs(api_key=API_KEY)

print("🔍 تست Speech-to-Text")
print("=" * 60)

# تست 1: فایل صوتی انگلیسی
print("\n🔍 تست 1: تبدیل صوت انگلیسی به متن")
try:
    with open("test_audio_en.mp3", "rb") as audio_file:
        result = client.speech_to_text.convert(
            file=audio_file,
            model_id="scribe_v1",
            language_code="eng"
        )
    
    print(f"✅ متن تشخیص داده شده: {result.text}")
    print(f"📊 تعداد کلمات: {len(result.text.split())}")
except Exception as e:
    print(f"❌ خطا: {e}")

# تست 2: فایل صوتی فارسی
print("\n🔍 تست 2: تبدیل صوت فارسی به متن")
try:
    with open("test_audio_fa.mp3", "rb") as audio_file:
        result_fa = client.speech_to_text.convert(
            file=audio_file,
            model_id="scribe_v1",
            language_code="fas"  # کد زبان فارسی (ISO 639-3)
        )
    
    print(f"✅ متن تشخیص داده شده: {result_fa.text}")
    print(f"📊 تعداد کلمات: {len(result_fa.text.split())}")
except Exception as e:
    print(f"❌ خطا: {e}")

print("\n" + "="*60)
print("✅ تست Speech-to-Text تمام شد!")
print("="*60)
