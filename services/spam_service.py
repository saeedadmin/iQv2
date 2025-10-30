#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Spam Service
سرویس مدیریت اسپم و بلاک خودکار
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# تنظیمات Anti-Spam
SPAM_MESSAGE_LIMIT = 8  # تعداد پیام مجاز
SPAM_TIME_WINDOW = 15   # در چند ثانیه


async def check_spam_and_handle(update: Update, context: ContextTypes.DEFAULT_TYPE, db_manager, bot_logger, admin_user_id: int) -> bool:
    """بررسی اسپم و مدیریت بلاک خودکار
    
    Returns:
        True: کاربر اسپم کرده و بلاک شد
        False: کاربر عادی است
    """
    user = update.effective_user
    
    # ادمین از چک اسپم معاف است
    if user.id == admin_user_id:
        return False
    
    # ثبت پیام کاربر در tracking
    db_manager.track_user_message(user.id, 'text')
    
    # بررسی تعداد پیام‌های اخیر
    recent_messages = db_manager.get_recent_message_count(user.id, SPAM_TIME_WINDOW)
    
    # اگر تعداد پیام‌ها از حد مجاز بیشتر شد
    if recent_messages > SPAM_MESSAGE_LIMIT:
        # بلاک کردن کاربر
        block_result = db_manager.block_user_for_spam(user.id)
        
        if block_result['success']:
            # لاگ بلاک اسپم
            bot_logger.log_admin_action(
                0,  # سیستم
                "AUTO_SPAM_BLOCK",
                target=f"User {user.id}",
                details=f"{recent_messages} پیام در {SPAM_TIME_WINDOW} ثانیه - سطح {block_result['warning_level']}"
            )
            
            # ارسال نوتیفیکیشن به کاربر
            await send_spam_block_notification(update, context, block_result)
            
            # ارسال نوتیفیکیشن به ادمین
            await send_admin_spam_notification(context, user, block_result, admin_user_id)
            
            return True
    
    return False


async def send_spam_block_notification(update: Update, context: ContextTypes.DEFAULT_TYPE, block_result: dict):
    """ارسال نوتیفیکیشن بلاک به کاربر"""
    try:
        warning_level = block_result['warning_level']
        block_duration = block_result['block_duration']
        is_permanent = block_result['is_permanent']
        
        if is_permanent:
            message = f"""🚫 **شما به طور دائمی بلاک شدید**

⚠️ **دلیل:** ارسال پیام‌های متوالی (اسپم)
📊 **سطح بلاک:** {warning_level} (دائمی)

❌ **این سومین بار است که به دلیل اسپم بلاک می‌شوید.**
دسترسی شما به طور دائم محدود شده است.

💡 برای بازگشایی حساب، با ادمین تماس بگیرید."""
        else:
            block_until_str = ""
            if block_result.get('block_until'):
                block_until_str = block_result['block_until'].strftime('%Y/%m/%d ساعت %H:%M')
            
            message = f"""⚠️ **شما موقتاً بلاک شدید**

🚫 **دلیل:** ارسال پیام‌های متوالی (اسپم)
⏰ **مدت بلاک:** {block_duration}
📊 **سطح بلاک:** {warning_level}
📅 **تا تاریخ:** {block_until_str}

💡 **توجه:**
• از ارسال پیام‌های پشت سر هم خودداری کنید
• بار بعد مدت بلاک طولانی‌تر خواهد بود
• در صورت تکرار، بلاک دائمی اعمال می‌شود

✅ پس از اتمام مدت بلاک، خودکار آزاد خواهید شد."""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطا در ارسال نوتیفیکیشن بلاک به کاربر: {e}")


async def send_admin_spam_notification(context: ContextTypes.DEFAULT_TYPE, user, block_result: dict, admin_user_id: int):
    """ارسال نوتیفیکیشن به ادمین"""
    try:
        import html
        
        warning_level = block_result['warning_level']
        block_duration = block_result['block_duration']
        
        # Escape کردن نام و یوزرنیم برای جلوگیری از خطای HTML
        safe_full_name = html.escape(user.full_name or 'ندارد')
        safe_username = html.escape(user.username or 'ندارد')
        
        message = f"""🚨 <b>هشدار اسپم - بلاک خودکار</b>

👤 <b>کاربر:</b>
• نام: {safe_full_name}
• یوزرنیم: @{safe_username}
• شناسه: <code>{user.id}</code>

⚠️ <b>اطلاعات بلاک:</b>
• سطح: {warning_level}
• مدت: {block_duration}

💡 از پنل ادمین می‌توانید این کاربر را مدیریت کنید."""
        
        await context.bot.send_message(
            chat_id=admin_user_id,
            text=message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"❌ خطا در ارسال نوتیفیکیشن اسپم به ادمین: {e}")
