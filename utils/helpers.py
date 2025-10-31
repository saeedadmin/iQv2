#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper Functions
توابع کمکی برای ربات تلگرام
"""

from telegram import Update


async def check_user_access(user_id: int, db_manager, admin_user_id: int) -> bool:
    """بررسی دسترسی کاربر به ربات"""
    # ادمین همیشه دسترسی دارد
    if user_id == admin_user_id:
        return True
    
    # بررسی فعال بودن ربات
    if not db_manager.is_bot_enabled():
        return False
    
    # بررسی بلاک بودن کاربر
    if db_manager.is_user_blocked(user_id):
        return False
    
    return True


async def send_access_denied_message(update: Update, user_id: int, db_manager) -> None:
    """ارسال پیام خطای عدم دسترسی"""
    if db_manager.is_user_blocked(user_id):
        await update.message.reply_text("🚫 شما از استفاده از این ربات محروم شده‌اید.")
    else:
        await update.message.reply_text("🔧 ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.")


async def safe_delete_message(message) -> None:
    """حذف ایمن پیام، در صورت خطا نادیده گرفتن"""
    try:
        await message.delete()
    except Exception:
        pass  # Ignore deletion errors
