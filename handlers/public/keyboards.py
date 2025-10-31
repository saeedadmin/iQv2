#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
کیبوردهای عمومی برای ربات تلگرام
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_markup() -> ReplyKeyboardMarkup:
    """کیبورد منوی اصلی"""
    keyboard = [
        [KeyboardButton("💰 ارزهای دیجیتال"), KeyboardButton("🔗 بخش عمومی")],
        [KeyboardButton("🤖 هوش مصنوعی"), KeyboardButton("⚽ بخش ورزش")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_public_section_markup() -> ReplyKeyboardMarkup:
    """کیبورد بخش عمومی"""
    keyboard = [
        [KeyboardButton("📺 اخبار عمومی")],
        [KeyboardButton("📰 مدیریت اشتراک اخبار")],
        [KeyboardButton("🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_ai_menu_markup() -> ReplyKeyboardMarkup:
    """کیبورد منوی هوش مصنوعی"""
    keyboard = [
        [KeyboardButton("💬 چت با هوش مصنوعی")],
        [KeyboardButton("📰 اخبار هوش مصنوعی")],
        [KeyboardButton("🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_ai_chat_mode_markup() -> ReplyKeyboardMarkup:
    """کیبورد حالت چت با هوش مصنوعی"""
    keyboard = [
        [KeyboardButton("🔙 بازگشت به منوی AI")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_crypto_menu_markup() -> ReplyKeyboardMarkup:
    """کیبورد منوی ارزهای دیجیتال"""
    keyboard = [
        [KeyboardButton("📊 قیمت‌های لحظه‌ای"), KeyboardButton("📰 اخبار کریپتو")],
        [KeyboardButton("📈 تحلیل TradingView")],
        [KeyboardButton("😨 شاخص ترس و طمع"), KeyboardButton("🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_sports_menu_markup() -> ReplyKeyboardMarkup:
    """کیبورد منوی ورزش"""
    keyboard = [
        [KeyboardButton("📰 اخبار ورزشی")],
        [KeyboardButton("📅 بازی‌های هفتگی")],
        [KeyboardButton("🔴 بازی‌های زنده")],
        [KeyboardButton("🔙 بازگشت به منوی اصلی")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
