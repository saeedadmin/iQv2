#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
کیبورد‌های ربات تلگرام
نویسنده: MiniMax Agent
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup

# کیبورد منوی اصلی - سه دکمه اصلی
main_menu_keyboard = [
    [KeyboardButton("💰 ارزهای دیجیتال")],
    [KeyboardButton("🔗 بخش عمومی")],
    [KeyboardButton("🤖 هوش مصنوعی")]
]

# کیبورد بخش عمومی
public_section_keyboard = [
    [KeyboardButton("📺 اخبار عمومی"), KeyboardButton("📰 مدیریت اشتراک اخبار")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش هوش مصنوعی
ai_menu_keyboard = [
    [KeyboardButton("💬 چت با هوش مصنوعی")],
    [KeyboardButton("📷 استخراج متن از عکس"), KeyboardButton("📰 اخبار هوش مصنوعی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش ارزهای دیجیتال
crypto_menu_keyboard = [
    [KeyboardButton("📈 تحلیل TradingView")],
    [KeyboardButton("😨 شاخص ترس و طمع"), KeyboardButton("💎 قیمت‌گذاری ارزها")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد حالت چت با AI (فقط دکمه خروج)
ai_chat_mode_keyboard = [
    [KeyboardButton("❌ خروج از چت")]
]

def get_main_menu_markup():
    """بازگرداندن کیبورد منوی اصلی"""
    return ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_public_section_markup():
    """بازگرداندن کیبورد بخش عمومی"""
    return ReplyKeyboardMarkup(public_section_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_menu_markup():
    """بازگرداندن کیبورد منوی هوش مصنوعی"""
    return ReplyKeyboardMarkup(ai_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_chat_mode_markup():
    """بازگرداندن کیبورد حالت چت با AI"""
    return ReplyKeyboardMarkup(ai_chat_mode_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_crypto_menu_markup():
    """بازگرداندن کیبورد بخش ارزهای دیجیتال"""
    return ReplyKeyboardMarkup(crypto_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)
