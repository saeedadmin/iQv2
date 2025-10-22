#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"BOT_TOKEN: {'Set' if os.getenv('BOT_TOKEN') else 'Not set'}")
print(f"ELEVENLABS_API_KEY: {'Set' if os.getenv('ELEVENLABS_API_KEY') else 'Not set'}")

if os.getenv('ELEVENLABS_API_KEY'):
    print(f"ELEVENLABS_API_KEY value: {os.getenv('ELEVENLABS_API_KEY')[:20]}...")

try:
    from ai_voice_handler import AIVoiceHandler
    handler = AIVoiceHandler()
    print('\n✅ AIVoiceHandler با موفقیت مقداردهی شد')
except Exception as e:
    print(f'\n❌ خطا در مقداردهی AIVoiceHandler: {e}')
    import traceback
    traceback.print_exc()
