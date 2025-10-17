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
    [KeyboardButton("📺 اخبار عمومی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش هوش مصنوعی
ai_menu_keyboard = [
    [KeyboardButton("📰 اخبار هوش مصنوعی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
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
