#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
کیبورد‌های ربات تلگرام
نویسنده: MiniMax Agent
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup

# کیبورد منوی اصلی
main_menu_keyboard = [
    [KeyboardButton("💰 ارزهای دیجیتال"), KeyboardButton("🤖 هوش مصنوعی")],
    [KeyboardButton("📊 پورتفولیو من"), KeyboardButton("📈 تحلیل تکنیکال")],
    [KeyboardButton("⚙️ تنظیمات"), KeyboardButton("📞 پشتیبانی")]
]

# کیبورد بخش هوش مصنوعی
ai_menu_keyboard = [
    [KeyboardButton("📰 اخبار هوش مصنوعی")],
    [KeyboardButton("🔙 بازگشت")]
]

# کیبورد بخش ارزهای دیجیتال
crypto_menu_keyboard = [
    [KeyboardButton("📊 قیمت لحظه‌ای"), KeyboardButton("📰 اخبار ارز")],
    [KeyboardButton("🔥 ارزهای ترند"), KeyboardButton("📈 نمودار قیمت")],
    [KeyboardButton("🔙 بازگشت")]
]

def get_main_menu_markup():
    """بازگرداندن کیبورد منوی اصلی"""
    return ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_menu_markup():
    """بازگرداندن کیبورد منوی هوش مصنوعی"""
    return ReplyKeyboardMarkup(ai_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_crypto_menu_markup():
    """بازگرداندن کیبورد منوی ارزهای دیجیتال"""
    return ReplyKeyboardMarkup(crypto_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)
