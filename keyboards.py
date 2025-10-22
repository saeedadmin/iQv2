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

# کیبورد بخش عمومی (پایه)
public_section_keyboard = [
    [KeyboardButton("📺 اخبار عمومی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش عمومی با دکمه دنبال کردن اخبار
public_section_keyboard_with_subscribe = [
    [KeyboardButton("📺 اخبار عمومی"), KeyboardButton("📰 دنبال کردن اخبار")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش عمومی با دکمه لغو اشتراک
public_section_keyboard_with_unsubscribe = [
    [KeyboardButton("📺 اخبار عمومی"), KeyboardButton("🔕 لغو اشتراک اخبار")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد بخش هوش مصنوعی
ai_menu_keyboard = [
    [KeyboardButton("💬 چت با هوش مصنوعی")],
    [KeyboardButton("📰 اخبار هوش مصنوعی")],
    [KeyboardButton("🔙 بازگشت به منوی اصلی")]
]

# کیبورد حالت چت با AI (فقط دکمه خروج)
ai_chat_mode_keyboard = [
    [KeyboardButton("❌ خروج از چت")]
]

def get_main_menu_markup():
    """بازگرداندن کیبورد منوی اصلی"""
    return ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_public_section_markup(is_subscribed: bool = False):
    """بازگرداندن کیبورد بخش عمومی (داینامیک بر اساس وضعیت اشتراک)"""
    if is_subscribed:
        return ReplyKeyboardMarkup(public_section_keyboard_with_unsubscribe, resize_keyboard=True, one_time_keyboard=False)
    else:
        return ReplyKeyboardMarkup(public_section_keyboard_with_subscribe, resize_keyboard=True, one_time_keyboard=False)

def get_ai_menu_markup():
    """بازگرداندن کیبورد منوی هوش مصنوعی"""
    return ReplyKeyboardMarkup(ai_menu_keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_ai_chat_mode_markup():
    """بازگرداندن کیبورد حالت چت با AI"""
    return ReplyKeyboardMarkup(ai_chat_mode_keyboard, resize_keyboard=True, one_time_keyboard=False)
