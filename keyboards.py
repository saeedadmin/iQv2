#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
کیبورد‌های ربات تلگرام
نویسنده: MiniMax Agent
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup

# کیبورد منوی اصلی - فقط دو دکمه
main_menu_keyboard = [
    [KeyboardButton("💰 ارزهای دیجیتال")],
    [KeyboardButton("🤖 هوش مصنوعی")]
]

# کیبورد بخش هوش مصنوعی
ai_menu_keyboard = [
    [KeyboardButton("📰 اخبار هوش مصنوعی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

def get_main_menu_markup():
    """بازگرداندن کیبورد منوی اصلی"""
    return ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_menu_markup():
    """بازگرداندن کیبورد منوی هوش مصنوعی"""
    return ReplyKeyboardMarkup(ai_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)
