#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Bot پیشرفته با پنل ادمین و مدیریت کاربران
نویسنده: MiniMax Agent

برای اجرا، environment variables زیر نیاز است:
- BOT_TOKEN: توکن ربات تلگرام
- ADMIN_USER_ID: شناسه عددی ادمین
"""

import logging
import asyncio
import datetime
import json
import os
import re
import difflib
import requests
import weakref
from aiohttp import web, ClientSession
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (Application, CommandHandler, ContextTypes, 
                          MessageHandler, filters, CallbackQueryHandler, ConversationHandler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from typing import Any, Dict, List, Optional, Tuple

# Load environment variables
load_dotenv()

# Choose database based on environment
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
    from database.database_postgres import PostgreSQLManager as DatabaseManager, DatabaseLogger
else:
    from database.database import DatabaseManager, DatabaseLogger

from handlers.admin.admin_panel import AdminPanel
from handlers.public import (
    get_main_menu_markup, 
    get_public_section_markup, 
    get_ai_menu_markup, 
    get_ai_chat_mode_markup,
    get_crypto_menu_markup,
    get_sports_menu_markup,
    get_sports_reminder_menu_markup,
    PublicMenuManager
)
from core.logger_system import bot_logger
from handlers.ai.ai_chat_handler import GeminiChatHandler, AIChatStateManager
from handlers.ai.ai_image_generator import AIImageGenerator
from handlers.ai.ocr_handler import OCRHandler
from handlers.sports import SportsHandler
from services.crypto_service import (
    fetch_fear_greed_index,
    download_fear_greed_chart,
    format_fear_greed_message
)
from services.spam_service import (
    check_spam_and_handle,
    send_spam_block_notification,
    send_admin_spam_notification,
    SPAM_MESSAGE_LIMIT,
    SPAM_TIME_WINDOW
)
from utils.helpers import (
    check_user_access as check_user_access_helper,
    send_access_denied_message
)

# Optional imports - TradingView Analysis
try:
    from handlers.ai.tradingview_analysis import TradingViewAnalysisFetcher
    TRADINGVIEW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TradingView Analysis غیرفعال: {e}")
    TradingViewAnalysisFetcher = None
    TRADINGVIEW_AVAILABLE = False

# تنظیمات logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
# کاهش لاگ‌های غیرضروری برای کاهش بار
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logging.getLogger("aiohttp.server").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# تنظیمات ربات از environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required")

ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 327459477))
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

# مقداردهی سیستم‌های اصلی
if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
    db_manager = DatabaseManager(DATABASE_URL)
else:
    db_manager = DatabaseManager()

db_logger = DatabaseLogger(db_manager)
admin_panel = AdminPanel(db_manager, ADMIN_USER_ID)
public_menu = PublicMenuManager(db_manager)

# Initialize AI systems
gemini_chat = GeminiChatHandler(db_manager=db_manager)
ai_chat_state = AIChatStateManager(db_manager)
ai_image_gen = AIImageGenerator()
ocr_handler = OCRHandler()

# Initialize Sports Handler
sports_handler = SportsHandler()

# Initialize TradingView fetcher if available
if TRADINGVIEW_AVAILABLE and TradingViewAnalysisFetcher:
    tradingview_fetcher = TradingViewAnalysisFetcher()
else:
    tradingview_fetcher = None

SPORTS_REMINDER_STATE_KEY = "sports_reminder_state"
SPORTS_REMINDER_CANCEL_WORDS = {"انصراف", "لغو", "cancel", "Cancel"}
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

# متغیرهای مکالمه
(BROADCAST_MESSAGE, USER_SEARCH, USER_ACTION, TRADINGVIEW_ANALYSIS) = range(4)

# بررسی دسترسی کاربر (wrapper for compatibility)
async def check_user_access(user_id: int) -> bool:
    """بررسی دسترسی کاربر به ربات"""
    return await check_user_access_helper(user_id, db_manager, ADMIN_USER_ID)

# Spam handling wrappers (using service functions)
async def check_spam_and_handle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Wrapper for spam checking service"""
    from services.spam_service import check_spam_and_handle as spam_check
    return await spam_check(update, context, db_manager, bot_logger, ADMIN_USER_ID)

# Keep original function name for compatibility
check_spam_and_handle = check_spam_and_handle_wrapper

# Functions for Fear & Greed Index
async def fetch_fear_greed_index():
    """دریافت شاخص ترس و طمع بازار کریپتو از alternative.me"""
    import aiohttp
    import json
    from datetime import datetime
    
    try:
        # API alternative.me برای شاخص ترس و طمع
        api_url = "https://api.alternative.me/fng/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and 'data' in data and len(data['data']) > 0:
                        index_data = data['data'][0]
                        
                        # استخراج اطلاعات
                        value = int(index_data['value'])
                        classification = index_data['value_classification']
                        timestamp = int(index_data['timestamp'])
                        
                        # تبدیل timestamp به تاریخ
                        update_time = datetime.fromtimestamp(timestamp)
                        
                        # تعیین ایموجی و رنگ براساس مقدار
                        if value <= 20:
                            emoji = "😱"
                            mood = "ترس شدید"
                            color = "🔴"
                        elif value <= 40:
                            emoji = "😰"
                            mood = "ترس"
                            color = "🟠"
                        elif value <= 60:
                            emoji = "😐"
                            mood = "خنثی"
                            color = "🟡"
                        elif value <= 80:
                            emoji = "😊"
                            mood = "طمع"
                            color = "🟢"
                        else:
                            emoji = "🤑"
                            mood = "طمع شدید"
                            color = "💚"
                        
                        return {
                            'value': value,
                            'classification': classification,
                            'mood_fa': mood,
                            'emoji': emoji,
                            'color': color,
                            'update_time': update_time,
                            'success': True
                        }
                    else:
                        raise Exception("Invalid API response format")
                else:
                    raise Exception(f"API request failed with status {response.status}")
                    
    except Exception as e:
        print(f"خطا در دریافت شاخص ترس و طمع: {e}")
        return {
            'value': 50,
            'classification': 'Neutral',
            'mood_fa': 'خنثی',
            'emoji': '😐',
            'color': '🟡',
            'update_time': datetime.now(),
            'success': False,
            'error': str(e)
        }

async def download_fear_greed_chart():
    """دانلود تصویر چارت شاخص ترس و طمع از منابع مختلف"""
    import aiohttp
    import os
    import tempfile
    
    # لیست منابع مختلف برای تصویر
    image_sources = [
        "https://alternative.me/crypto/fear-and-greed-index.png",
        "https://alternative.me/images/fng/crypto-fear-and-greed-index.png", 
        "https://api.alternative.me/fng/png"
    ]
    
    # استفاده از پوشه موقت سیستم برای جلوگیری از مشکلات مجوز
    temp_dir = tempfile.gettempdir()
    chart_path = os.path.join(temp_dir, "fear_greed_chart.png")
    
    # Headers برای شبیه‌سازی درخواست مرورگر
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Accept': 'image/png,image/webp,image/jpeg,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    
    for i, chart_url in enumerate(image_sources, 1):
        try:
            print(f"تلاش {i}: دانلود از {chart_url}")
            
            async with aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(chart_url) as response:
                    print(f"وضعیت پاسخ: {response.status}")
                    
                    if response.status == 200:
                        content = await response.read()
                        print(f"حجم محتوا: {len(content)} بایت")
                        
                        # بررسی اینکه محتوا یک تصویر واقعی است
                        if len(content) > 1000:  # حداقل 1KB برای تصویر
                            # بررسی magic bytes برای PNG
                            if content.startswith(b'\x89PNG') or content.startswith(b'\xff\xd8\xff'):
                                with open(chart_path, 'wb') as f:
                                    f.write(content)
                                
                                if os.path.exists(chart_path) and os.path.getsize(chart_path) > 1000:
                                    print(f"✅ تصویر با موفقیت دانلود شد: {chart_path}")
                                    return chart_path
                                else:
                                    print("❌ مشکل در ذخیره فایل")
                            else:
                                print("❌ محتوا تصویر معتبری نیست")
                        else:
                            print(f"❌ حجم محتوا خیلی کم است: {len(content)} بایت")
                    else:
                        print(f"❌ کد خطای HTTP: {response.status}")
                        
        except Exception as e:
            print(f"❌ خطا در منبع {i}: {e}")
            continue
    
    print("❌ هیچ منبعی کار نکرد - ایجاد تصویر ساده...")
    return await create_simple_fear_greed_image()

async def create_simple_fear_greed_image():
    """ایجاد تصویر ساده شاخص ترس و طمع"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import math
        import os
        
        # دریافت مقدار فعلی شاخص
        index_data = await fetch_fear_greed_index()
        value = index_data.get('value', 50)
        
        # ایجاد canvas
        width, height = 400, 300
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # رنگ براساس مقدار
        if value <= 25:
            color = '#FF0000'  # قرمز - ترس شدید
        elif value <= 45:
            color = '#FF8000'  # نارنجی - ترس
        elif value <= 55:
            color = '#FFFF00'  # زرد - خنثی
        elif value <= 75:
            color = '#80FF00'  # سبز روشن - طمع
        else:
            color = '#00FF00'  # سبز - طمع شدید
        
        # رسم دایره اصلی
        center_x, center_y = width // 2, height // 2 + 20
        radius = 100
        
        # رسم قوس نیم دایره
        for angle in range(180):
            end_x = center_x + radius * math.cos(math.radians(180 - angle))
            end_y = center_y - radius * math.sin(math.radians(180 - angle))
            
            # رنگ گرادیانت
            progress = angle / 180
            if progress < 0.25:
                arc_color = '#FF0000'
            elif progress < 0.45:
                arc_color = '#FF8000'
            elif progress < 0.55:
                arc_color = '#FFFF00'
            elif progress < 0.75:
                arc_color = '#80FF00'
            else:
                arc_color = '#00FF00'
            
            draw.line([(center_x, center_y), (end_x, end_y)], fill=arc_color, width=3)
        
        # رسم عقربه
        needle_angle = 180 - (value * 180 / 100)
        needle_x = center_x + (radius - 10) * math.cos(math.radians(needle_angle))
        needle_y = center_y - (radius - 10) * math.sin(math.radians(needle_angle))
        draw.line([(center_x, center_y), (needle_x, needle_y)], fill='black', width=5)
        
        # نوشتن متن
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # نوشتن مقدار
        text = f"{value}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((center_x - text_width//2, center_y + 30), text, fill='black', font=font)
        
        # نوشتن برچسب‌ها
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            small_font = ImageFont.load_default()
        
        draw.text((30, center_y + 10), "Fear", fill='red', font=small_font)
        draw.text((width - 70, center_y + 10), "Greed", fill='green', font=small_font)
        
        # ذخیره فایل در پوشه موقت سیستم
        import tempfile
        temp_dir = tempfile.gettempdir()
        chart_path = os.path.join(temp_dir, "fear_greed_chart.png")
        img.save(chart_path, 'PNG')
        
        if os.path.exists(chart_path):
            print(f"✅ تصویر ساده ایجاد شد: {chart_path}")
            return chart_path
        else:
            print("❌ مشکل در ایجاد تصویر ساده")
            return None
            
    except Exception as e:
        print(f"❌ خطا در ایجاد تصویر ساده: {e}")
        return None

def format_fear_greed_message(index_data):
    """فرمت کردن پیام شاخص ترس و طمع"""
    
    if not index_data['success']:
        return f"""😨 شاخص ترس و طمع بازار کریپتو

❌ متاسفانه در حال حاضر امکان دریافت اطلاعات وجود ندارد.

🔄 لطفاً چند دقیقه بعد دوباره تلاش کنید.

📊 منبع: Alternative.me"""

    # توضیحات براساس مقدار شاخص
    if index_data['value'] <= 20:
        description = """🔍 وضعیت بازار:
• سطح ترس بسیار بالا در بازار
• احتمال فرصت خرید مناسب
• سرمایه‌گذاران بسیار محتاط هستند
• قیمت‌ها ممکن است به کف رسیده باشند"""
    elif index_data['value'] <= 40:
        description = """🔍 وضعیت بازار:
• سطح ترس نسبتاً بالا
• بازار در حالت فروش
• سرمایه‌گذاران نگران هستند  
• ممکن است فرصت خرید باشد"""
    elif index_data['value'] <= 60:
        description = """🔍 وضعیت بازار:
• بازار در حالت خنثی و متعادل
• عدم وجود احساسات شدید
• تصمیم‌گیری براساس تحلیل تکنیکال
• وضعیت نرمال بازار"""
    elif index_data['value'] <= 80:
        description = """🔍 وضعیت بازار:
• سطح طمع نسبتاً بالا
• بازار در حالت خرید
• سرمایه‌گذاران خوش‌بین هستند
• احتمال اصلاح قیمت وجود دارد"""
    else:
        description = """🔍 وضعیت بازار:
• سطح طمع بسیار بالا
• احتمال حباب قیمتی
• سرمایه‌گذاران بسیار خوش‌بین
• زمان مناسب برای فروش ممکن است"""

    # فرمت پیام نهایی
    message = f"""😨 شاخص ترس و طمع بازار کریپتو

{index_data['color']} <b>مقدار فعلی: {index_data['value']}/100</b>

{index_data['emoji']} <b>وضعیت: {index_data['mood_fa']}</b>

{description}

📅 آخرین به‌روزرسانی: {index_data['update_time'].strftime('%Y/%m/%d - %H:%M')}

📊 منبع: Alternative.me Fear & Greed Index

⚠️ توجه: این شاخص صرفاً جهت اطلاع‌رسانی است و توصیه سرمایه‌گذاری نمی‌باشد."""

    return message





# Signal message formatting removed - will be re-implemented later

# Handler برای دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پیام خوش‌آمدگویی هنگام اجرای دستور /start"""
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 شما از استفاده از این ربات محروم شده‌اید.")
        else:
            await update.message.reply_text("🔧 ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.")
        return

    # پاک کردن هر وضعیت ناتمام مربوط به یادآوری
    context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)

    # اضافه/به‌روزرسانی کاربر در دیتابیس
    db_manager.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=(user.id == ADMIN_USER_ID)
    )
    
    # لاگ عملیات
    bot_logger.log_user_action(user.id, "START_COMMAND", f"کاربر {user.first_name} ربات را شروع کرد")
    
    welcome_message = f"""
سلام {user.mention_html()}! 👋

به ربات خوش آمدید!

از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:

💰 ارزهای دیجیتال: قیمت‌های لحظه‌ای و اخبار کریپتو
🔗 بخش عمومی: اخبار عمومی از منابع معتبر
🤖 هوش مصنوعی: آخرین اخبار AI
    """
    
    # استفاده از کیبورد جدید
    reply_markup = get_main_menu_markup()
    
    # نمایش پیام خوش آمدگویی
    await update.message.reply_html(
        welcome_message,
        reply_markup=reply_markup
    )
# Handler برای دستور /help
# Help command removed - not needed

# Handler برای دستور /menu
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش منوی اصلی"""
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 شما از استفاده از این ربات محروم شده‌اید.")
        else:
            await update.message.reply_text("🔧 ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.")
        return
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    # لاگ عملیات
    bot_logger.log_user_action(user.id, "MENU_COMMAND", f"کاربر {user.first_name} منو را مشاهده کرد")
    
    message = """
🏠 *منوی اصلی*

به ربات خوش آمدید! از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:

💰 *ارزهای دیجیتال:* قیمت‌های لحظه‌ای ارزها، تتر و دلار
📰 *اخبار:* اخبار کریپتو و عمومی از منابع معتبر
🤖 *هوش مصنوعی:* آخرین اخبار AI
    """
    
    # استفاده از کیبورد جدید
    reply_markup = get_main_menu_markup()
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Handler برای دستور /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش وضعیت ربات"""
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        return
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    # دریافت اطلاعات کاربر از دیتابیس
    user_data = db_manager.get_user(user.id)
    stats = db_manager.get_user_stats()
    
    if user_data:
        join_date = datetime.datetime.fromisoformat(user_data['join_date'].replace('Z', '+00:00'))
        last_activity = datetime.datetime.fromisoformat(user_data['last_activity'].replace('Z', '+00:00'))
        days_since_join = (datetime.datetime.now() - join_date).days
    else:
        join_date = datetime.datetime.now()
        last_activity = datetime.datetime.now()
        days_since_join = 0
    
    bot_status = "🟢 فعال" if db_manager.is_bot_enabled() else "🔴 غیرفعال"
    user_status = "🚫 بلاک شده" if db_manager.is_user_blocked(user.id) else "✅ فعال"
    admin_badge = " 👨‍💼" if user.id == ADMIN_USER_ID else ""
    
    # محاسبه uptime به فرمت قابل خواندن
    uptime_delta = datetime.datetime.now() - admin_panel.bot_start_time
    uptime_hours = int(uptime_delta.total_seconds() // 3600)
    uptime_minutes = int((uptime_delta.total_seconds() % 3600) // 60)
    uptime_str = f"{uptime_hours} ساعت و {uptime_minutes} دقیقه"
    
    # Escape کردن کاراکترهای خاص HTML
    import html
    safe_name = html.escape(user.full_name or "بدون نام")
    safe_username = html.escape(user.username or "ندارد")
    
    status_text = f"""
📊 <b>وضعیت ربات و کاربر</b>

<b>🤖 وضعیت ربات:</b>
• ربات: {bot_status}
• مدت اجرا: {uptime_str}
• کل کاربران: {stats['total']}

<b>👤 اطلاعات شما:{admin_badge}</b>
• نام: {safe_name}
• نام کاربری: @{safe_username}
• شناسه: <code>{user.id}</code>
• وضعیت: {user_status}

<b>📈 آمار فعالیت شما:</b>
• تاریخ عضویت: {join_date.strftime('%Y/%m/%d %H:%M')}
• آخرین فعالیت: {last_activity.strftime('%Y/%m/%d %H:%M')}
• روزهای عضویت: {days_since_join}
• تعداد پیام‌ها: {user_data['message_count'] if user_data else 0}

<b>🌐 اطلاعات سرور:</b>
• زمان سرور: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
• وضعیت اتصال: ✅ متصل
    """
    await update.message.reply_text(status_text, parse_mode='HTML')

# Signal command handler removed - will be re-implemented later

# Handler برای دستور /admin (فقط برای ادمین)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پنل مدیریت پیشرفته - فقط برای ادمین"""
    user = update.effective_user
    
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید.")
        return
    
    # لاگ دسترسی ادمین
    bot_logger.log_admin_action(user.id, "ADMIN_PANEL_ACCESS")
    
    # Escape کردن نام برای جلوگیری از خطای HTML
    import html
    safe_first_name = html.escape(user.first_name or "ادمین")
    
    welcome_text = f"""
🔧 <b>پنل مدیریت ربات</b>

خوش آمدید {safe_first_name}! 👨‍💼

این پنل امکانات کاملی برای مدیریت ربات فراهم می‌کند:

🖥️ <b>سیستم:</b> مدیریت منابع و وضعیت
👥 <b>کاربران:</b> مدیریت و آمارگیری کاربران  
📊 <b>آمار:</b> گزارش‌های تفصیلی
📋 <b>لاگ‌ها:</b> رصد فعالیت‌ها
📢 <b>پیام همگانی:</b> ارسال به همه کاربران
⚙️ <b>تنظیمات:</b> پیکربندی ربات

یک بخش را انتخاب کنید:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=admin_panel.create_main_menu_keyboard(),
        parse_mode='HTML'
    )

# Handler برای شروع فرآیند تحلیل TradingView
async def tradingview_analysis_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند تحلیل TradingView"""
    help_message = """
📈 *تحلیل کامیونیتی TradingView*

آخرین تحلیل‌های کاربران حرفه‌ای TradingView را دریافت کنید!

✅ *فرمت مورد قبول:*
• فقط جفت ارز با USDT به صورت حروف کوچک
• مثال: `btcusdt`, `ethusdt`, `solusdt`

📝 *مثال‌های صحیح:*
• btcusdt (بیت کوین)
• ethusdt (اتریوم) 
• solusdt (سولانا)
• adausdt (کاردانو)
• bnbusdt (بایننس کوین)
• xrpusdt (ریپل)
• dogeusdt (دوج کوین)
• linkusdt (چین لینک)
• ltcusdt (لایت کوین)
• dotusdt (پولکادات)
• avaxusdt (اولانچ)

⚠️ *نکته مهم:* فقط حروف کوچک، بدون فاصله یا نشانه
💡 *راهنما:* جفت ارز مورد نظر خود را تایپ کنید

برای لغو /cancel بفرستید
    """
    
    await update.message.reply_text(help_message, parse_mode='Markdown')
    return TRADINGVIEW_ANALYSIS

async def tradingview_analysis_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش درخواست تحلیل TradingView"""
    user = update.effective_user
    message_text = update.message.text
    
    if message_text.startswith('/cancel'):
        await update.message.reply_text("❌ تحلیل TradingView لغو شد.")
        return ConversationHandler.END
    
    # اعتبارسنجی فرمت ورودی
    crypto_pair_pattern = r'^[a-z]+usdt$'
    message_clean = message_text.lower().strip()
    
    # اول بررسی کن که آیا فرمت درست است
    if re.match(crypto_pair_pattern, message_clean) and len(message_clean) >= 6:
        # چک کردن در دسترس بودن TradingView
        if not tradingview_fetcher:
            await update.message.reply_text("❌ سرویس تحلیل TradingView در دسترس نیست.")
            return ConversationHandler.END
        
        # نمایش پیام در حال بارگذاری
        loading_message = await update.message.reply_text("⏳ در حال دریافت آخرین تحلیل کامیونیتی از TradingView...\n\nلطفاً چند ثانیه صبر کنید.")
        
        try:
            # دریافت تحلیل از TradingView
            analysis_data = await tradingview_fetcher.fetch_latest_analysis(message_clean)
            
            if analysis_data.get('success'):
                # فرمت کردن پیام
                analysis_message = tradingview_fetcher.format_analysis_message(analysis_data)
                
                # ارسال پیام تحلیل
                await loading_message.delete()
                
                # بررسی نوع تحلیل (دو تحلیل یا یکی)
                if 'popular_analysis' in analysis_data and 'recent_analysis' in analysis_data:
                    # فرمت کردن پیام‌های جداگانه برای هر تحلیل
                    crypto_emojis = {
                        'btc': '₿', 'eth': '🔷', 'sol': '⚡', 'ada': '₳', 'bnb': '🟡',
                        'xrp': '🔷', 'doge': '🐕', 'link': '🔗', 'ltc': 'Ł', 'dot': '●', 'avax': '🔺'
                    }
                    crypto_emoji = crypto_emojis.get(analysis_data['crypto'].lower(), '💰')
                    
                    # پیام جدیدترین تحلیل
                    recent = analysis_data['recent_analysis']
                    recent_message = f"""🕐 *جدیدترین تحلیل {analysis_data['symbol']}*

{crypto_emoji} *عنوان:* {recent['title']}

📄 *توضیحات:*
{recent['description'][:400]}{'...' if len(recent['description']) > 400 else ''}

👤 *نویسنده:* {recent['author']}"""

                    # پیام محبوب‌ترین تحلیل  
                    popular = analysis_data['popular_analysis']
                    popular_message = f"""🔥 *محبوب‌ترین تحلیل {analysis_data['symbol']}*

{crypto_emoji} *عنوان:* {popular['title']}

📄 *توضیحات:*
{popular['description'][:400]}{'...' if len(popular['description']) > 400 else ''}

👤 *نویسنده:* {popular['author']}"""

                    # ارسال جدیدترین تحلیل (با یا بدون عکس)
                    if recent.get('image_url'):
                        try:
                            await update.message.reply_photo(
                                photo=recent['image_url'],
                                caption=recent_message,
                                parse_mode='Markdown'
                            )
                        except:
                            await update.message.reply_text(
                                recent_message,
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                            )
                    else:
                        await update.message.reply_text(
                            recent_message,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                    
                    # ارسال محبوب‌ترین تحلیل (با یا بدون عکس)
                    if popular.get('image_url'):
                        try:
                            await update.message.reply_photo(
                                photo=popular['image_url'],
                                caption=popular_message,
                                parse_mode='Markdown'
                            )
                        except:
                            await update.message.reply_text(
                                popular_message,
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                            )
                    else:
                        await update.message.reply_text(
                            popular_message,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                            
                else:
                    # یک تحلیل (مثل قبل)
                    if analysis_data.get('image_url'):
                        # ارسال با عکس
                        try:
                            await update.message.reply_photo(
                                photo=analysis_data['image_url'],
                                caption=analysis_message,
                                parse_mode='Markdown'
                            )
                        except Exception:
                            # اگر عکس کار نکرد، فقط متن بفرست
                            await update.message.reply_text(
                                analysis_message,
                                parse_mode='Markdown',
                                disable_web_page_preview=True
                            )
                    else:
                        # ارسال بدون عکس
                        await update.message.reply_text(
                            analysis_message,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
            else:
                # خطا در دریافت تحلیل (پیام خطا از tradingview_fetcher می‌آید)
                await loading_message.edit_text(analysis_data.get('error', 'خطا در دریافت تحلیل'))
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت تحلیل TradingView:\n{str(e)}"
            await loading_message.edit_text(error_message)
        
        return ConversationHandler.END
    else:
        # فرمت اشتباه - نمایش پیام خطا
        wrong_format_patterns = [
            r'^[a-zA-Z]+/[a-zA-Z]+$',  # مثل BTC/USDT
            r'^[A-Z]{2,6}$',           # مثل BTC، ETH (حروف بزرگ کوتاه)
            r'^[a-z]{2,6}$',           # مثل btc، eth (حروف کوچک کوتاه، بدون usdt)
            r'^[a-zA-Z]+-[a-zA-Z]+$',  # مثل BTC-USDT
            r'^[a-zA-Z]+_[a-zA-Z]+$',  # مثل BTC_USDT
            r'^[a-zA-Z]+\s+[a-zA-Z]+$', # مثل BTC USDT
        ]
        
        # اگر کاربر فرمت اشتباه وارد کرده (ولی شبیه ارز است)
        format_looks_like_crypto = any(re.match(pattern, message_text.strip()) for pattern in wrong_format_patterns)
        
        if format_looks_like_crypto or len(message_text.strip()) >= 3:
            error_message = """❌ **فرمت نادرست!**

✅ **فرمت صحیح:** `btcusdt` (حروف کوچک، چسبیده)

📝 **مثال‌های معتبر:**
• `btcusdt` - بیت کوین
• `ethusdt` - اتریوم  
• `solusdt` - سولانا
• `adausdt` - کاردانو
• `bnbusdt` - بایننس کوین
• `xrpusdt` - ریپل
• `dogeusdt` - دوج کوین

⚠️ **توجه:** فقط حروف کوچک، بدون فاصله یا نشانه خاص

لطفاً دوباره تلاش کنید یا /cancel برای لغو بفرستید."""
            
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return TRADINGVIEW_ANALYSIS
        else:
            await update.message.reply_text("❌ ورودی نامعتبر. لطفاً نام ارز را به فرمت صحیح وارد کنید یا /cancel برای لغو بفرستید.")
            return TRADINGVIEW_ANALYSIS

# Handler برای لغو conversation
async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو هر conversation فعال"""
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# کالبک هندلر برای دکمه‌های اشتراک اخبار
async def news_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت callback query برای دکمه‌های اشتراک اخبار"""
    query = update.callback_query
    user = update.effective_user
    
    # تایید callback query
    await query.answer()
    
    if query.data == "news_sub_enable":
        # فعال کردن اشتراک
        success = db_manager.enable_news_subscription(user.id)
        
        if success:
            bot_logger.log_user_action(user.id, "NEWS_SUBSCRIPTION_ENABLED", "اشتراک اخبار فعال شد")
            
            confirmation_message = """
✅ **اشتراک اخبار فعال شد!**

🎉 از این پس ربات هر روز 3 بار به صورت خودکار آخرین اخبار را برای شما ارسال می‌کند.

⏰ **زمان‌های ارسال:**
• 🌅 8:00 صبح
• 🌇 14:00 ظهر
• 🌃 20:00 شب

🔕 برای لغو اشتراک، از دکمه "📰 مدیریت اشتراک اخبار" استفاده کنید.
            """
            
            # حذف دکمه‌های inline و نمایش پیام تایید
            await query.edit_message_text(
                text=confirmation_message,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="❌ خطا در فعال‌سازی اشتراک. لطفاً دوباره تلاش کنید."
            )
    
    elif query.data == "news_sub_disable":
        # غیرفعال کردن اشتراک
        success = db_manager.disable_news_subscription(user.id)
        
        if success:
            bot_logger.log_user_action(user.id, "NEWS_SUBSCRIPTION_DISABLED", "اشتراک اخبار لغو شد")
            
            success_message = """
✅ **اشتراک اخبار لغو شد**

دیگر اخبار خودکار برای شما ارسال نخواهد شد.

شما می‌توانید هر زمان دوباره فعال کنید.
            """
            
            await query.edit_message_text(
                text=success_message,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="❌ خطا در لغو اشتراک. لطفاً دوباره تلاش کنید."
            )
    
    elif query.data == "news_sub_back":
        # بازگشت
        bot_logger.log_user_action(user.id, "NEWS_SUBSCRIPTION_BACK", "بازگشت از مدیریت اشتراک")
        
        await query.edit_message_text(
            text="🔙 بازگشت به بخش عمومی",
            parse_mode='Markdown'
        )

# تابع ارسال خودکار اخبار برای مشترکان
async def send_scheduled_news(context: ContextTypes.DEFAULT_TYPE) -> None:
    """ارسال خودکار اخبار برای مشترکان (فراخوانی توسط scheduler)"""
    try:
        logger.info("📡 شروع ارسال خودکار اخبار...")
        
        # دریافت لیست مشترکان
        subscribers = db_manager.get_news_subscribers()
        
        if not subscribers:
            logger.info("⚠️ هیچ مشترکی برای اخبار وجود ندارد")
            return
        
        logger.info(f"👥 تعداد مشترکان: {len(subscribers)}")
        
        # دریافت آخرین اخبار
        from handlers.public.public_menu import PublicMenuManager
        public_menu_temp = PublicMenuManager(db_manager)
        news_list = await public_menu_temp.fetch_general_news()
        
        if not news_list:
            logger.error("❌ خطا در دریافت اخبار برای ارسال خودکار")
            return
        
        # فرمت کردن پیام اخبار با تابع صحیح از public_menu
        news_message = public_menu_temp.format_general_news_message(news_list)
        
        # اضافه کردن یک هدر برای ارسال خودکار
        header = f"""🔔 **اخبار خودکار - {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}**

"""
        full_message = header + news_message
        
        # شمارنده برای ارسال موفق و ناموفق
        success_count = 0
        failed_count = 0
        
        # ارسال برای هر مشترک
        for user_id in subscribers:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=full_message,
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
                success_count += 1
                logger.info(f"✅ اخبار برای کاربر {user_id} ارسال شد")
                
                # تاخیر کوتاه برای جلوگیری از flood
                await asyncio.sleep(0.05)  # 50ms delay
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"⚠️ خطا در ارسال برای کاربر {user_id}: {e}")
                
                # اگر کاربر ربات رو بلاک کرده (احتمالاً Forbidden error)
                if "Forbidden" in str(e):
                    # غیرفعال کردن اشتراک برای این کاربر
                    db_manager.disable_news_subscription(user_id)
                    logger.info(f"🚫 اشتراک کاربر {user_id} به دلیل بلاک کردن ربات غیرفعال شد")
        
        # لاگ نتیجه نهایی
        logger.info(
            f"✅ ارسال خودکار اخبار کامل شد | "
            f"موفق: {success_count} | ناموفق: {failed_count}"
        )
        
        # ارسال گزارش به ادمین
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"""📡 **گزارش ارسال خودکار اخبار**

⏰ زمان: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}
✅ موفق: {success_count}
❌ ناموفق: {failed_count}
👥 جمع مشترکان: {len(subscribers)}""",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ خطای کلی در ارسال خودکار اخبار: {e}")


def _chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _format_favorites_summary(favorites: List[Dict[str, Any]]) -> str:
    if not favorites:
        return "📭 هیچ تیمی در لیست یادآوری نیست."

    lines = ["📋 تیم‌های ثبت‌شده:"]
    for idx, fav in enumerate(favorites, start=1):
        created_at = fav.get('created_at')
        created_str = ''
        if created_at:
            try:
                if isinstance(created_at, datetime.datetime):
                    created_local = created_at.astimezone(TEHRAN_TZ) if created_at.tzinfo else TEHRAN_TZ.localize(created_at)
                    created_str = created_local.strftime('%Y/%m/%d')
            except Exception:
                created_str = ''
        date_part = f" - ثبت: {created_str}" if created_str else ''
        lines.append(f"{idx}. {fav.get('team_name')} ({fav.get('league_name')}){date_part}")

    return "\n".join(lines)


def _format_upcoming_reminders(reminders: List[Dict[str, Any]]) -> str:
    if not reminders:
        return "⏰ هنوز یادآوری فعالی ثبت نشده است."

    lines = ["⏰ بازی‌های آتی:"]
    for idx, reminder in enumerate(reminders[:5], start=1):
        match_dt = reminder.get('match_datetime')
        if match_dt:
            try:
                if match_dt.tzinfo is None:
                    match_dt = pytz.UTC.localize(match_dt)
                match_local = match_dt.astimezone(TEHRAN_TZ)
                match_str = match_local.strftime('%Y/%m/%d %H:%M')
            except Exception:
                match_str = 'نامشخص'
        else:
            match_str = 'نامشخص'

        opponent = reminder.get('opponent_team_name') or 'حریف'
        league_name = reminder.get('league_name') or 'لیگ'
        lines.append(f"{idx}. {reminder.get('team_name')} vs {opponent} ({league_name}) - {match_str}")

    if len(reminders) > 5:
        lines.append("...")

    return "\n".join(lines)


def _build_reminder_panel_text(header: Optional[str], favorites: List[Dict[str, Any]], reminders: List[Dict[str, Any]]) -> str:
    sections: List[str] = []
    if header:
        sections.append(header)
    sections.append(_format_favorites_summary(favorites))
    sections.append(_format_upcoming_reminders(reminders))
    return "\n\n".join(sections)


def build_sports_league_keyboard(include_back: bool = True) -> InlineKeyboardMarkup:
    league_keys = sports_handler.league_order + ['champions_league']
    buttons: List[List[InlineKeyboardButton]] = []
    current_row: List[InlineKeyboardButton] = []

    for key in league_keys:
        if key not in sports_handler.league_ids:
            continue
        label = sports_handler.league_display_names.get(key, key)
        current_row.append(InlineKeyboardButton(label, callback_data=f"sports_reminder_league_{key}"))
        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []

    if current_row:
        buttons.append(current_row)

    if include_back:
        buttons.append([InlineKeyboardButton("⬅️ انتخاب لیگ دیگر", callback_data="sports_reminder_back_to_leagues")])

    return InlineKeyboardMarkup(buttons)


def build_sports_team_keyboard(league_key: str, teams: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    current_row: List[InlineKeyboardButton] = []

    for team in teams:
        team_id = team.get('team_id')
        team_name = team.get('team_name')
        if not team_id or not team_name:
            continue

        callback_data = f"sports_reminder_team_{league_key}_{team_id}"
        current_row.append(InlineKeyboardButton(team_name, callback_data=callback_data))

        if len(current_row) == 2:
            buttons.append(current_row)
            current_row = []

    if current_row:
        buttons.append(current_row)

    buttons.append([
        InlineKeyboardButton("⬅️ بازگشت به انتخاب لیگ", callback_data="sports_reminder_back_to_leagues"),
        InlineKeyboardButton("❌ انصراف", callback_data="sports_reminder_cancel")
    ])

    return InlineKeyboardMarkup(buttons)


def build_sports_favorites_keyboard(favorites: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []

    for fav in favorites:
        team_id = fav.get('team_id')
        team_name = fav.get('team_name')
        if not team_id or not team_name:
            continue
        callback_data = f"sports_reminder_remove_{team_id}"
        buttons.append([InlineKeyboardButton(f"❌ حذف {team_name}", callback_data=callback_data)])

    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="sports_reminder_back_to_leagues")])

    return InlineKeyboardMarkup(buttons)


def build_sports_settings_message(favorites: List[Dict[str, Any]]) -> str:
    if not favorites:
        summary = "📭 لیست یادآوری شما خالی است."
    else:
        lines = ["📋 تیم‌های ثبت‌شده در یادآوری:"]
        for idx, fav in enumerate(favorites, start=1):
            created_at = fav.get('created_at')
            created_str = ''
            if created_at:
                try:
                    if isinstance(created_at, datetime.datetime):
                        created_local = created_at.astimezone(TEHRAN_TZ) if created_at.tzinfo else TEHRAN_TZ.localize(created_at)
                        created_str = created_local.strftime('%Y/%m/%d')
                except Exception:
                    created_str = ''
            date_part = f" - ثبت: {created_str}" if created_str else ''
            lines.append(f"{idx}. {fav['team_name']} ({fav['league_name']}){date_part}")
        summary = "\n".join(lines)

    instructions = (
        "\n\n➕ برای افزودن تیم: یکی از لیگ‌های زیر را انتخاب کنید و سپس نام تیم را دقیقاً مطابق نمایش ارسال کنید."
        "\n➖ برای حذف تیم: پیام را به شکل `حذف نام تیم` ارسال کنید."
        "\n❌ برای لغو افزودن تیم، عبارت 'لغو' را بفرستید."
    )

    return summary + instructions


def build_user_reminders_message(reminders: List[Dict[str, Any]]) -> str:
    if not reminders:
        return "📭 هیچ یادآوری فعالی برای شما ثبت نشده است."

    lines = ["⏰ یادآوری‌های فعال:"]
    for idx, reminder in enumerate(reminders, start=1):
        match_dt = reminder.get('match_datetime')
        reminder_dt = reminder.get('reminder_datetime')

        try:
            if match_dt:
                if match_dt.tzinfo is None:
                    match_dt = pytz.UTC.localize(match_dt)
                match_dt = match_dt.astimezone(TEHRAN_TZ)
        except Exception:
            pass

        try:
            if reminder_dt:
                if reminder_dt.tzinfo is None:
                    reminder_dt = pytz.UTC.localize(reminder_dt)
                reminder_dt = reminder_dt.astimezone(TEHRAN_TZ)
        except Exception:
            pass

        match_str = match_dt.strftime('%Y/%m/%d %H:%M') if match_dt else 'نامشخص'
        reminder_str = reminder_dt.strftime('%Y/%m/%d %H:%M') if reminder_dt else match_str

        lines.append(
            f"{idx}. {reminder['team_name']} vs {reminder['opponent_team_name']}"
            f"\n   لیگ: {reminder['league_name']}"
            f"\n   شروع بازی: {match_str}"
            f"\n   زمان یادآوری: {reminder_str}"
        )

    return "\n\n".join(lines)


async def send_sports_main_menu(update: Update) -> None:
    message = (
        "⚽ **بخش ورزش**\n\n"
        "به دنیای فوتبال خوش آمدید! ⚽️\n\n"
        "🔍 **خدمات موجود:**\n"
        "• 📰 **اخبار ورزشی:** آخرین اخبار فوتبال ایران و جهان\n"
        "• 📅 **بازی‌های هفتگی:** برنامه بازی‌های لیگ ایران و اروپا\n"
        "• 🔴 **بازی‌های زنده:** نتایج لحظه‌ای بازی‌ها"
    )

    await update.message.reply_text(
        message,
        reply_markup=get_sports_menu_markup(),
        parse_mode='Markdown'
    )


async def send_sports_reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
    message = (
        "⏰ *یادآوری بازی*"
        "\n\nبا این بخش می‌توانید تیم‌های محبوب خود را اضافه کنید تا ربات شروع بازی‌های آن‌ها را به شما یادآوری کند."
        "\n\nاز دکمه‌های زیر برای مدیریت استفاده کنید."
    )
    await update.message.reply_text(
        message,
        reply_markup=get_sports_reminder_menu_markup(),
        parse_mode='Markdown'
    )


async def handle_sports_reminder_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
    user = update.effective_user
    favorites = db_manager.get_sports_favorite_teams(user.id)
    reminders = db_manager.get_user_match_reminders(user.id, include_sent=False)
    message = _build_reminder_panel_text("⚙️ تنظیمات یادآوری", favorites, reminders)
    await update.message.reply_text(
        message,
        reply_markup=build_sports_league_keyboard(include_back=False)
    )


async def handle_sports_reminder_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    reminders = db_manager.get_user_match_reminders(user.id, include_sent=False)
    favorites = db_manager.get_sports_favorite_teams(user.id)
    message = _build_reminder_panel_text("📋 یادآوری‌های من", favorites, reminders)
    reply_markup = build_sports_favorites_keyboard(favorites) if favorites else None
    await update.message.reply_text(message, reply_markup=reply_markup)


async def handle_sports_league_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    data = query.data

    if data == "sports_reminder_back_to_leagues":
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        favorites = db_manager.get_sports_favorite_teams(user.id)
        reminders = db_manager.get_user_match_reminders(user.id, include_sent=False)
        message = _build_reminder_panel_text("⚙️ تنظیمات یادآوری", favorites, reminders)
        await query.answer()
        await query.message.edit_text(
            message,
            reply_markup=build_sports_league_keyboard(include_back=False)
        )
        return

    if data == "sports_reminder_cancel":
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        await query.answer(text="عملیات لغو شد.", show_alert=False)
        return

    if data.startswith('sports_reminder_team_'):
        payload = data.replace('sports_reminder_team_', '', 1)
        if '_' not in payload:
            await query.answer(text="داده نامعتبر است", show_alert=True)
            return
        league_key, team_id_str = payload.rsplit('_', 1)
        try:
            team_id = int(team_id_str)
        except ValueError:
            await query.answer(text="شناسه تیم نامعتبر است", show_alert=True)
            return

        state = context.user_data.get(SPORTS_REMINDER_STATE_KEY)
        if not state or state.get('league_key') != league_key:
            await query.answer(text="ابتدا لیگ را انتخاب کنید", show_alert=True)
            return

        teams = state.get('teams', [])
        team_match = next((team for team in teams if team.get('team_id') == team_id), None)
        if not team_match:
            await query.answer(text="تیم پیدا نشد", show_alert=True)
            return

        league_name = state.get('league_name', league_key)
        league_id = sports_handler.league_ids.get(league_key)
        if not league_id:
            await query.answer(text="لیگ نامعتبر است", show_alert=True)
            return

        user_record = db_manager.get_user(user.id)
        is_admin = bool(user_record and user_record.get('is_admin'))
        success, msg = db_manager.add_sports_favorite_team(
            user.id,
            league_id,
            league_name,
            team_match['team_id'],
            team_match['team_name'],
            max_teams=10,
            bypass_limit=is_admin
        )

        favorites = db_manager.get_sports_favorite_teams(user.id)
        upcoming_reminders = db_manager.get_user_match_reminders(user.id, include_sent=False)
        header = f"✅ تیم ثبت شد: {team_match['team_name']}" if success else f"⚠️ {msg}"
        body = _build_reminder_panel_text(header, favorites, upcoming_reminders)

        await query.answer(text="تیم ثبت شد" if success else None, show_alert=False)
        await query.message.edit_text(
            body,
            reply_markup=build_sports_team_keyboard(league_key, teams)
        )

        if success:
            bot_logger.log_user_action(user.id, "SPORTS_TEAM_ADDED", team_match['team_name'])
        return

    if data.startswith('sports_reminder_remove_'):
        team_id_raw = data.replace('sports_reminder_remove_', '', 1)
        try:
            team_id = int(team_id_raw)
        except ValueError:
            await query.answer(text="شناسه نامعتبر است", show_alert=True)
            return

        success, msg = db_manager.remove_sports_favorite_team_by_id(user.id, team_id)
        if success:
            db_manager.delete_match_reminders_for_team(user.id, team_id)

        favorites = db_manager.get_sports_favorite_teams(user.id)
        reminders = db_manager.get_user_match_reminders(user.id, include_sent=False)
        message = _build_reminder_panel_text(msg if success else "⚠️ " + msg, favorites, reminders)
        reply_markup = build_sports_favorites_keyboard(favorites) if favorites else None

        await query.answer()
        await query.message.edit_text(message, reply_markup=reply_markup)
        return

    if not data.startswith('sports_reminder_league_'):
        await query.answer(text="دستور نامعتبر", show_alert=True)
        return

    league_key = data.replace('sports_reminder_league_', '', 1)

    await query.answer()

    if league_key not in sports_handler.league_ids:
        await query.message.reply_text("❌ لیگ انتخابی معتبر نیست.")
        return

    league_name = sports_handler.league_display_names.get(league_key, league_key)

    team_data = await sports_handler.get_league_teams(league_key)
    if not team_data.get('success'):
        error_message = team_data.get('error', 'خطا در دریافت تیم‌ها')
        await query.message.reply_text(f"❌ {error_message}")
        return

    teams = team_data.get('teams', [])
    if not teams:
        await query.message.reply_text("⚠️ هیچ تیمی برای این لیگ یافت نشد.")
        return

    context.user_data[SPORTS_REMINDER_STATE_KEY] = {
        'league_key': league_key,
        'league_name': league_name,
        'teams': teams,
        'requested_at': datetime.datetime.now().isoformat()
    }

    await query.message.edit_text(
        f"✅ لیگ انتخاب شد: {league_name}\n\nیکی از تیم‌های زیر را انتخاب کنید:",
        reply_markup=build_sports_team_keyboard(league_key, teams)
    )


async def process_team_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, state: Dict[str, Any], user_record: Optional[Dict[str, Any]]) -> bool:
    message_text = update.message.text.strip()

    if message_text in SPORTS_REMINDER_CANCEL_WORDS:
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        await update.message.reply_text("✅ عملیات افزودن تیم لغو شد.")
        return True

    teams = state.get('teams', [])
    team_match = next((team for team in teams if team['team_name'].lower() == message_text.lower()), None)

    if not team_match:
        suggestions = difflib.get_close_matches(message_text, [team['team_name'] for team in teams], n=3, cutoff=0.7)
        suggestion_text = "\n".join(f"• {sugg}" for sugg in suggestions) if suggestions else ""
        extra_hint = f"\n\nشاید منظور شما یکی از موارد زیر باشد:\n{suggestion_text}" if suggestion_text else ""
        await update.message.reply_text(
            "❌ تیم وارد شده در فهرست وجود ندارد. لطفاً دقیقاً مطابق فهرست ارسال کنید یا 'لغو' را بفرستید." + extra_hint
        )
        return True

    league_key = state.get('league_key')
    league_id = sports_handler.league_ids.get(league_key)
    league_name = state.get('league_name', league_key)

    if not league_id:
        await update.message.reply_text("❌ خطا در تشخیص لیگ. لطفاً دوباره گزینه لیگ را انتخاب کنید.")
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        return True

    is_admin = bool(user_record and user_record.get('is_admin'))
    success, msg = db_manager.add_sports_favorite_team(
        update.effective_user.id,
        league_id,
        league_name,
        team_match['team_id'],
        team_match['team_name'],
        max_teams=10,
        bypass_limit=is_admin
    )

    await update.message.reply_text(msg)

    if success:
        bot_logger.log_user_action(update.effective_user.id, "SPORTS_TEAM_ADDED", team_match['team_name'])
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        favorites = db_manager.get_sports_favorite_teams(update.effective_user.id)
        settings_message = build_sports_settings_message(favorites)
        await update.message.reply_text(
            settings_message,
            reply_markup=build_sports_league_keyboard()
        )

    return True


def serialize_weekly_fixtures_for_cache(fixtures: Dict[str, Any]) -> Dict[str, Any]:
    leagues = {}
    for key, league in fixtures.get('leagues', {}).items():
        matches_serialized = []
        for match in league.get('matches', []):
            match_dt = match.get('datetime')
            match_iso = match_dt.isoformat() if isinstance(match_dt, datetime.datetime) else None
            matches_serialized.append({
                'fixture_id': match.get('fixture_id'),
                'home_team_id': match.get('home_team_id'),
                'home_team': match.get('home_team'),
                'away_team_id': match.get('away_team_id'),
                'away_team': match.get('away_team'),
                'league_id': match.get('league_id'),
                'league_name': match.get('league_name'),
                'datetime': match_iso,
                'status': match.get('status'),
                'venue': match.get('venue')
            })

        leagues[key] = {
            'name': league.get('name'),
            'count': league.get('count'),
            'matches': matches_serialized
        }

    return {
        'success': fixtures.get('success', False),
        'total_matches': fixtures.get('total_matches', 0),
        'period': fixtures.get('period', ''),
        'leagues': leagues
    }


def format_match_reminder_message(reminder: Dict[str, Any]) -> str:
    match_dt = reminder.get('match_datetime')
    if match_dt:
        if match_dt.tzinfo is None:
            match_dt = pytz.UTC.localize(match_dt)
        match_dt_local = match_dt.astimezone(TEHRAN_TZ)
        match_time_str = match_dt_local.strftime('%Y/%m/%d %H:%M')
    else:
        match_time_str = 'نامشخص'

    league_name = reminder.get('league_name', 'نامشخص')
    team_name = reminder.get('team_name', 'تیم شما')
    opponent = reminder.get('opponent_team_name', 'حریف')

    message = (
        f"⏰ *یادآوری بازی*\n\n"
        f"🏆 لیگ: {league_name}\n"
        f"⚔️ {team_name} vs {opponent}\n"
        f"🕒 زمان شروع: {match_time_str}\n\n"
        f"موفق باشید!"
    )

    return message


def _compute_week_range(base_date: datetime.datetime) -> Tuple[datetime.date, datetime.date]:
    base_date_local = base_date
    days_since_saturday = (base_date_local.weekday() + 2) % 7
    week_start_dt = (base_date_local - datetime.timedelta(days=days_since_saturday)).date()
    week_end_dt = week_start_dt + datetime.timedelta(days=6)
    return week_start_dt, week_end_dt


async def _upsert_weekly_fixtures_cache(base_date: Optional[datetime.datetime] = None) -> Optional[Dict[str, Any]]:
    utc_now = datetime.datetime.now(pytz.UTC)
    tehran_now = base_date or utc_now.astimezone(TEHRAN_TZ)

    week_start_dt, week_end_dt = _compute_week_range(tehran_now)

    fixtures = await sports_handler.get_all_weekly_fixtures(base_date=tehran_now)

    if fixtures.get('success'):
        cache_payload = serialize_weekly_fixtures_for_cache(fixtures)
        db_manager.upsert_weekly_fixtures_cache(week_start_dt, week_end_dt, cache_payload)
        return fixtures

    logger.warning(f"⚠️ عدم موفقیت در دریافت فیکسچرهای هفتگی: {fixtures.get('error')}")
    cached = db_manager.get_weekly_fixtures_cache(week_start_dt, week_end_dt)
    if cached and cached.get('payload'):
        logger.info("♻️ استفاده از کش فیکسچرهای هفتگی قبلی")
        return cached['payload']

    return None


def _get_cached_weekly_fixtures(base_date: Optional[datetime.datetime] = None) -> Optional[Dict[str, Any]]:
    utc_now = datetime.datetime.now(pytz.UTC)
    tehran_now = base_date or utc_now.astimezone(TEHRAN_TZ)

    week_start_dt, week_end_dt = _compute_week_range(tehran_now)
    cached = db_manager.get_weekly_fixtures_cache(week_start_dt, week_end_dt)
    if cached and cached.get('payload'):
        return cached['payload']
    return None


# ثبت تابع بروزرسانی کش برای استفاده در پنل ادمین
admin_panel.set_weekly_cache_refresher(_upsert_weekly_fixtures_cache)


def _hydrate_match_datetime(match: Dict[str, Any]) -> Optional[datetime.datetime]:
    match_dt = match.get('datetime')
    if isinstance(match_dt, str):
        try:
            match_dt_utc = datetime.datetime.fromisoformat(match_dt)
            if match_dt_utc.tzinfo is None:
                match_dt_utc = pytz.UTC.localize(match_dt_utc)
            return match_dt_utc
        except Exception:
            return None
    if isinstance(match_dt, datetime.datetime):
        return match_dt if match_dt.tzinfo else pytz.UTC.localize(match_dt)
    return None


def _generate_user_team_reminders(user_id: int, favorites: List[Dict[str, Any]], leagues_data: Dict[str, Any]) -> int:
    created_count = 0

    for fav in favorites:
        db_manager.delete_match_reminders_for_team(user_id, fav['team_id'])

    for league_key, league_info in leagues_data.items():
        matches = league_info.get('matches', [])
        for match in matches:
            match_dt_utc = _hydrate_match_datetime(match)

            for fav in favorites:
                team_id = fav['team_id']
                if match.get('home_team_id') != team_id and match.get('away_team_id') != team_id:
                    continue

                opponent_team_id = match['away_team_id'] if match.get('home_team_id') == team_id else match.get('home_team_id')
                opponent_team_name = match['away_team'] if match.get('home_team_id') == team_id else match['home_team']

                extra_info = {
                    'league_key': league_key,
                    'opponent_id': opponent_team_id
                }

                success, _ = db_manager.create_match_reminder(
                    user_id=user_id,
                    fixture_id=match.get('fixture_id'),
                    team_id=team_id,
                    team_name=fav['team_name'],
                    opponent_team_id=opponent_team_id,
                    opponent_team_name=opponent_team_name,
                    league_id=match.get('league_id'),
                    league_name=match.get('league_name'),
                    match_datetime=match_dt_utc,
                    reminder_datetime=match_dt_utc,
                    extra_info=extra_info
                )

                if success:
                    created_count += 1

    return created_count


async def refresh_weekly_sports_reminders(app: Application) -> None:
    try:
        fixtures = await _upsert_weekly_fixtures_cache()
        if not fixtures:
            return

        users = db_manager.get_users_with_sports_favorites()
        if not users:
            logger.info("ℹ️ کاربری برای یادآوری‌های ورزشی ثبت نشده است.")
            return

        leagues_data = fixtures.get('leagues', {})

        for user_id in users:
            favorites = db_manager.get_sports_favorite_teams(user_id)
            if not favorites:
                continue

            created_count = _generate_user_team_reminders(user_id, favorites, leagues_data)
            logger.info(f"✅ یادآوری‌های جدید برای کاربر {user_id} ثبت شد: {created_count}")

    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی یادآوری‌های ورزشی: {e}")


async def refresh_daily_sports_reminders(app: Application) -> None:
    try:
        fixtures = _get_cached_weekly_fixtures()
        if not fixtures:
            logger.warning("⚠️ کش فیکسچرهای هفتگی یافت نشد؛ یادآوری روزانه اجرا نشد")
            return

        users = db_manager.get_users_with_sports_favorites()
        if not users:
            return

        leagues_data = fixtures.get('leagues', {})

        for user_id in users:
            favorites = db_manager.get_sports_favorite_teams(user_id)
            if not favorites:
                continue

            created_count = _generate_user_team_reminders(user_id, favorites, leagues_data)
            logger.info(f"🔁 یادآوری‌های روزانه برای کاربر {user_id} به‌روزرسانی شد: {created_count}")

    except Exception as e:
        logger.error(f"❌ خطا در به‌روزرسانی روزانه یادآوری‌های ورزشی: {e}")


async def process_due_sports_reminders(app: Application) -> None:
    try:
        now_utc = datetime.datetime.now(pytz.UTC)
        due_reminders = db_manager.get_pending_match_reminders(now_utc)
        if not due_reminders:
            return

        for reminder in due_reminders:
            message = format_match_reminder_message(reminder)
            try:
                await app.bot.send_message(
                    chat_id=reminder['user_id'],
                    text=message,
                    parse_mode='Markdown'
                )
                db_manager.mark_match_reminder_sent(reminder['id'])
            except Exception as send_error:
                logger.error(f"❌ خطا در ارسال یادآوری بازی برای کاربر {reminder['user_id']}: {send_error}")

    except Exception as e:
        logger.error(f"❌ خطا در پردازش یادآوری‌های ورزشی: {e}")
# Handler برای پیام‌های متنی (echo)
async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """راهنمایی برای پیام‌های ناشناخته"""
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 شما از استفاده از این ربات محروم شده‌اید.")
        else:
            await update.message.reply_text("🔧 ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.")
        return
    
    # 🚨 چک اسپم - قبل از هر عملیاتی
    is_spam = await check_spam_and_handle(update, context)
    if is_spam:
        # کاربر اسپم کرده و بلاک شده - دیگر پردازش نشه
        return
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    # لاگ پیام
    db_logger.log_user_action(user.id, "MESSAGE_SENT", f"پیام ارسال شد: {update.message.text[:50]}...")
    
    message_text = update.message.text
    user_data = db_manager.get_user(user.id)
    
    # لیست دکمه‌های کیبورد که نباید به AI فرستاده بشن
    keyboard_buttons = [
        "💰 ارزهای دیجیتال", "🔗 بخش عمومی", "🤖 هوش مصنوعی",
        "🔙 بازگشت به منوی اصلی", "📺 اخبار عمومی", "📰 مدیریت اشتراک اخبار",
        "💬 چت با هوش مصنوعی", "📰 اخبار هوش مصنوعی", "🔙 بازگشت به منوی AI",
        "📊 قیمت‌های لحظه‌ای", "📰 اخبار کریپتو", "📈 تحلیل TradingView",
        "😨 شاخص ترس و طمع", "❌ خروج از چت",
        "⚽ بخش ورزش", "📰 اخبار ورزشی", "📅 بازی‌های هفتگی",
        "🔴 بازی‌های زنده", "⏰ یادآوری بازی", "⚙️ تنظیمات یادآوری",
        "📋 یادآوری‌های من", "🔙 بازگشت به ورزش"
    ]
    
    # 🚨 بررسی حالت چت با AI - اگر کاربر در چت است، پیام را به AI بفرستید
    # استثنا: همه دکمه‌های کیبورد که باید مستقیم پردازش بشن
    if ai_chat_state.is_in_chat(user.id) and message_text not in keyboard_buttons:
        bot_logger.log_user_action(user.id, "AI_CHAT_MESSAGE", f"پیام در چت: {message_text[:50]}...")
        
        # نمایش پیام "در حال تایپ..."
        typing_message = await update.message.reply_text("🤖 در حال پردازش پیام شما...")
        
        try:
            # ارسال پیام به AI
            result = await asyncio.to_thread(
                gemini_chat.send_message_with_history,
                user.id,
                message_text
            )
            
            # حذف پیام "در حال تایپ..."
            await typing_message.delete()
            
            if result['success']:
                # فرمت پاسخ برای تلگرام
                formatted_response = gemini_chat.format_response_for_telegram(result['response'])
                
                # ارسال پاسخ AI
                await update.message.reply_text(
                    formatted_response,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                
                bot_logger.log_user_action(user.id, "AI_CHAT_RESPONSE_SUCCESS", f"پاسخ موفق - توکن‌ها: {result['tokens_used']}")
                
                # افزایش شمارنده پیام
                ai_chat_state.increment_message_count(user.id)
                
            else:
                # مدیریت خطاهای مختلف
                error_type = result.get('error_type', 'unknown')
                error_msg = result.get('error', '')
                
                if error_type == 'rate_limit':
                    wait_time = int(error_msg.split(':')[1]) if ':' in error_msg else 60
                    await update.message.reply_text(
                        f"⏱️ محدودیت تعداد پیام! لطفاً {wait_time} ثانیه صبر کنید."
                    )
                elif error_type == 'server_overload':
                    await update.message.reply_text(
                        "⚠️ سرور AI در حال حاضر شلوغ است. لطفاً چند دقیقه بعد تلاش کنید."
                    )
                elif error_type == 'timeout':
                    await update.message.reply_text(
                        "⏱️ زمان پاسخ به پایان رسید. لطفاً دوباره تلاش کنید."
                    )
                elif error_type == 'network_error':
                    await update.message.reply_text(
                        "🌐 مشکل در اتصال به اینترنت. لطفاً اتصال خود را بررسی کنید."
                    )
                elif error_type == 'client_error':
                    await update.message.reply_text(
                        "❌ خطا در درخواست. لطفاً پیام خود را ساده‌تر کنید."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ خطای غیرمنتظره: {error_msg}"
                    )
                
                bot_logger.log_user_action(user.id, "AI_CHAT_RESPONSE_ERROR", f"خطا: {error_type}")
        
        except Exception as e:
            # حذف پیام "در حال تایپ..." در صورت خطا
            try:
                await typing_message.delete()
            except:
                pass
            
            logger.error(f"❌ خطا در پردازش پیام چت AI: {e}")
            await update.message.reply_text(
                "❌ متاسفانه در پردازش پیام شما خطایی رخ داد. لطفاً دوباره تلاش کنید."
            )
        
        return
    
    # بررسی دکمه‌های کیبورد
    if message_text == "💰 ارزهای دیجیتال":
        # نمایش منوی ارزهای دیجیتال
        message = """
💰 *بخش ارزهای دیجیتال*

🔍 *خدمات موجود:*
• 📈 قیمت‌های لحظه‌ای ارزهای اصلی
• 📊 بررسی تغییرات 24 ساعته
• 💰 قیمت تتر و دلار به تومان
• 🚀 بیشترین صعود و نزول بازار
• 📰 آخرین اخبار کریپتو از منابع معتبر


از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:
        """
        
        # کیبورد منوی ارزهای دیجیتال
        crypto_keyboard = [
            [KeyboardButton("📊 قیمت‌های لحظه‌ای"), KeyboardButton("📰 اخبار کریپتو")],
            [KeyboardButton("📈 تحلیل TradingView")],
            [KeyboardButton("😨 شاخص ترس و طمع"), KeyboardButton("🔙 بازگشت به منوی اصلی")]
        ]
        reply_markup = ReplyKeyboardMarkup(crypto_keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📊 قیمت‌های لحظه‌ای":
        # نمایش پیام در حال بارگذاری
        loading_message = await update.message.reply_text("⏳ در حال دریافت قیمت‌های لحظه‌ای...\n\nلطفاً چند ثانیه صبر کنید.")
        
        try:
            # دریافت داده‌ها
            crypto_data = await public_menu.fetch_crypto_prices()
            message = public_menu.format_crypto_message(crypto_data)
            
            # ویرایش پیام با نتایج (بدون parse_mode برای جلوگیری از خطای entities)
            await loading_message.edit_text(message)
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت قیمت‌ها:\n{str(e)}"
            await loading_message.edit_text(error_message)
        
        return
    
    elif message_text == "📰 اخبار کریپتو":
        # نمایش پیام در حال بارگذاری
        loading_message = await update.message.reply_text("⏳ در حال دریافت آخرین اخبار کریپتو...\n\nلطفاً چند ثانیه صبر کنید.")
        
        try:
            # دریافت اخبار
            news_list = await public_menu.fetch_crypto_news()
            message = public_menu.format_crypto_news_message(news_list)
            
            # ویرایش پیام با نتایج
            await loading_message.edit_text(
                message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت اخبار:\n{str(e)}"
            await loading_message.edit_text(error_message)
        
        return
    
    elif message_text == "📈 تحلیل TradingView":
        return await tradingview_analysis_start(update, context)
    

    
    elif message_text == "😨 شاخص ترس و طمع":
        # نمایش پیام در حال بارگذاری
        loading_message = await update.message.reply_text("⏳ در حال دریافت آخرین شاخص ترس و طمع بازار...\n\nلطفاً چند ثانیه صبر کنید.")
        
        try:
            # دریافت شاخص ترس و طمع
            index_data = await fetch_fear_greed_index()
            message = format_fear_greed_message(index_data)
            
            # دانلود تصویر چارت
            chart_path = await download_fear_greed_chart()
            
            # حذف پیام loading
            await loading_message.delete()
            
            # ارسال پیام همراه با تصویر
            if chart_path and os.path.exists(chart_path):
                try:
                    # بررسی حجم فایل
                    file_size = os.path.getsize(chart_path)
                    print(f"📊 ارسال تصویر شاخص - حجم: {file_size} بایت")
                    
                    # ارسال تصویر همراه با متن در کپشن
                    with open(chart_path, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=message,
                            parse_mode='HTML'
                        )
                    print("✅ عکس شاخص ترس و طمع با موفقیت ارسال شد")
                    
                except Exception as photo_error:
                    print(f"❌ خطا در ارسال عکس: {photo_error}")
                    # اگر ارسال عکس ناموفق بود، متن را ارسال کن
                    await update.message.reply_text(
                        f"🔄 **مشکل در نمایش تصویر**\n\n{message}\n\n_تصویر در حال حاضر در دسترس نیست_",
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                
                # حذف فایل موقت
                try:
                    os.remove(chart_path)
                    print("🗑️ فایل موقت حذف شد")
                except:
                    pass
            else:
                print("❌ هیچ تصویری دانلود نشد - ارسال فقط متن")
                # اگر تصویر دانلود نشد، فقط متن ارسال کن
                await update.message.reply_text(
                    f"📊 **شاخص ترس و طمع بازار کریپتو**\n\n{message}\n\n_⚠️ تصویر در حال حاضر در دسترس نیست_",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            
        except Exception as e:
            error_message = f"❌ خطا در دریافت شاخص ترس و طمع:\n{str(e)}"
            print(f"خطای کلی در شاخص ترس و طمع: {e}")
            try:
                await loading_message.edit_text(error_message)
            except:
                await update.message.reply_text(error_message)
        
        return
    
    elif message_text == "🔙 بازگشت به منوی اصلی":
        # بازگشت به منوی اصلی
        welcome_message = """
سلام! 👋

به ربات خوش آمدید!

از دکمه‌های زیر برای دسترسی به خدمات استفاده کنید:

💰 ارزهای دیجیتال: قیمت‌های لحظه‌ای و اخبار کریپتو
🔗 بخش عمومی: اخبار عمومی از منابع معتبر  
🤖 هوش مصنوعی: آخرین اخبار AI
        """
        
        # استفاده از کیبورد جدید
        reply_markup = get_main_menu_markup()
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )
        return
    
    elif message_text == "🔗 بخش عمومی":
        # نمایش منوی بخش عمومی
        bot_logger.log_user_action(user.id, "PUBLIC_SECTION_ACCESS", "ورود به بخش عمومی")
        
        message = """
🔗 *بخش عمومی*

اطلاعات و اخبار عمومی! 📺

🔍 *خدمات موجود:*
• 📺 اخبار عمومی از منابع معتبر فارسی
• 📰 مدیریت اشتراک اخبار: دریافت خودکار اخبار روزانه

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        # نمایش کیبورد ساده
        reply_markup = get_public_section_markup()
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📰 مدیریت اشتراک اخبار":
        # مدیریت اشتراک اخبار
        bot_logger.log_user_action(user.id, "NEWS_SUBSCRIPTION_MANAGE", "ورود به مدیریت اشتراک اخبار")
        
        # پیام توضیحی
        info_message = """
📰 **مدیریت اشتراک اخبار خودکار**

با فعال کردن این قابلیت، ربات هر روز **3 بار** به صورت خودکار سرتیتر اخبار روز را برای شما ارسال می‌کند:

⏰ **زمان‌بندی ارسال:**
• 🌅 صبح: 8:00
• 🌇 ظهر: 14:00
• 🌃 شب: 20:00

📰 **محتوا:**
سرتیتر آخرین اخبار روز از منابع معتبر فارسی

✅ **رایگان** و **بدون محدودیت**

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        # دکمه‌های فعال/غیرفعال و بازگشت
        keyboard = [
            [InlineKeyboardButton("✅ فعال‌سازی اشتراک", callback_data="news_sub_enable")],
            [InlineKeyboardButton("❌ غیرفعال‌سازی اشتراک", callback_data="news_sub_disable")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="news_sub_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            info_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "🤖 هوش مصنوعی":
        # نمایش منوی هوش مصنوعی
        bot_logger.log_user_action(user.id, "AI_MENU_ACCESS", "ورود به بخش هوش مصنوعی")
        
        message = """
🤖 *بخش هوش مصنوعی*

به دنیای AI خوش آمدید! 🚀

🔍 *خدمات موجود:*
• 💬 *چت با هوش مصنوعی:* پرسش و پاسخ با Gemini 2.0
• 📰 *اخبار AI:* آخرین پیشرفت‌ها و اخبار

از دکمه‌های زیر برای استفاده از خدمات انتخاب کنید:
        """
        
        # استفاده از کیبورد AI
        reply_markup = get_ai_menu_markup()
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "⚽ بخش ورزش":
        bot_logger.log_user_action(user.id, "SPORTS_MENU_ACCESS", "ورود به بخش ورزش")
        await send_sports_main_menu(update)
        return

    elif message_text == "⏰ یادآوری بازی":
        bot_logger.log_user_action(user.id, "SPORTS_REMINDER_MENU", "باز کردن منوی یادآوری")
        await send_sports_reminder_menu(update, context)
        return

    elif message_text == "⚙️ تنظیمات یادآوری":
        bot_logger.log_user_action(user.id, "SPORTS_REMINDER_SETTINGS", "نمایش تنظیمات یادآوری")
        await handle_sports_reminder_settings(update, context)
        return

    elif message_text == "📋 یادآوری‌های من":
        bot_logger.log_user_action(user.id, "SPORTS_REMINDER_LIST", "درخواست لیست یادآوری‌ها")
        await handle_sports_reminder_list(update, context)
        return

    elif message_text == "🔙 بازگشت به ورزش":
        context.user_data.pop(SPORTS_REMINDER_STATE_KEY, None)
        await send_sports_main_menu(update)
        return

    
    elif message_text == "📰 اخبار ورزشی":
        bot_logger.log_user_action(user.id, "SPORTS_NEWS_REQUEST", "درخواست اخبار ورزشی")
        
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار ورزشی...")
        
        try:
            news_result = await sports_handler.get_persian_news(limit=10)
            news_message = sports_handler.format_news_message(news_result)
            
            await loading_message.delete()
            await update.message.reply_text(
                news_message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        except Exception as e:
            await loading_message.delete()
            await update.message.reply_text(
                f"❌ خطا در دریافت اخبار:\n{str(e)}"
            )
        return
    
    elif message_text == "📅 بازی‌های هفتگی":
        bot_logger.log_user_action(user.id, "SPORTS_FIXTURES_REQUEST", "درخواست برنامه بازی‌ها")
        
        loading_message = await update.message.reply_text("🔄 در حال دریافت برنامه بازی‌های همه لیگ‌ها...")
        
        try:
            # دریافت همه لیگ‌ها یکجا
            all_fixtures = await sports_handler.get_all_weekly_fixtures()
            fixtures_message = sports_handler.format_all_fixtures_message(all_fixtures)
            
            await loading_message.delete()
            
            # ارسال در یک پیام
            await update.message.reply_text(
                fixtures_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            await loading_message.delete()
            await update.message.reply_text(
                f"❌ خطا در دریافت برنامه بازی‌ها:\n{str(e)}"
            )
        return
    
    elif message_text == "🔴 بازی‌های زنده":
        bot_logger.log_user_action(user.id, "SPORTS_LIVE_REQUEST", "درخواست بازی‌های زنده")
        
        loading_message = await update.message.reply_text("🔄 در حال بررسی بازی‌های زنده...")
        
        try:
            live_result = await sports_handler.get_live_matches()
            live_message = sports_handler.format_live_matches_message(live_result)
            
            await loading_message.delete()
            await update.message.reply_text(
                live_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            await loading_message.delete()
            await update.message.reply_text(
                f"❌ خطا در دریافت بازی‌های زنده:\n{str(e)}"
            )
        return
    
    elif message_text == "📺 اخبار عمومی":
        bot_logger.log_user_action(user.id, "GENERAL_NEWS_REQUEST", "درخواست اخبار عمومی")
        
        # نمایش پیام "در حال بارگذاری"
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار روز از منابع متعدد...")
        
        try:
            # دریافت اخبار عمومی از منابع متعدد
            news_list = await public_menu.fetch_general_news()
            news_text = public_menu.format_general_news_message(news_list)
            
            # حذف پیام loading
            await loading_message.delete()
            
            # ارسال اخبار
            await update.message.reply_text(
                news_text,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            
        except Exception as e:
            # حذف پیام loading در صورت خطا
            try:
                await loading_message.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"❌ خطا در دریافت اخبار عمومی:\n{str(e)}",
                parse_mode='Markdown'
            )
        
        return
    
    elif message_text == "💬 چت با هوش مصنوعی":
        # شروع چت با AI
        bot_logger.log_user_action(user.id, "AI_CHAT_START", "شروع چت با هوش مصنوعی")
        
        # فعال کردن حالت چت
        ai_chat_state.start_chat(user.id)
        
        welcome_message = """
🤖 *چت با هوش مصنوعی Gemini*

سلام! من آماده پاسخگویی به سوالات شما هستم 🚀

💬 *چگونه استفاده کنم？*
• هر سوالی دارید بپرسید
• می‌توانم در موضوعات مختلف کمک کنم
• به فارسی و انگلیسی پاسخ می‌دهم

❌ برای خروج از چت، دکمه "خروج از چت" را بزنید.

❓ سوال خود را بپرسید:
        """
        
        # نمایش کیبورد حالت چت (فقط دکمه خروج)
        reply_markup = get_ai_chat_mode_markup()
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "❌ خروج از چت":
        # خروج از چت AI
        if ai_chat_state.is_in_chat(user.id):
            ai_chat_state.end_chat(user.id)
            bot_logger.log_user_action(user.id, "AI_CHAT_END", "خروج از چت با AI")
            
            # دریافت آمار چت
            stats = ai_chat_state.get_chat_stats(user.id)
            
            goodbye_message = f"""
👋 *خداحافظی!*

چت با هوش مصنوعی پایان یافت.

📊 *آمار جلسه چت:*
• تعداد پیام‌ها: {stats['message_count']}

برای شروع مجدد چت، دکمه "💬 چت با هوش مصنوعی" را بزنید.
            """
            
            # برگشت به منوی AI
            reply_markup = get_ai_menu_markup()
            
            await update.message.reply_text(
                goodbye_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "⚠️ شما در حال حاضر در چت با AI نیستید.",
                reply_markup=get_ai_menu_markup()
            )
        return
    
    elif message_text == "📰 اخبار هوش مصنوعی":
        bot_logger.log_user_action(user.id, "AI_NEWS_REQUEST", "درخواست اخبار هوش مصنوعی")
        
        # نمایش پیام "در حال بارگذاری"
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار هوش مصنوعی...")
        
        try:
            # دریافت اخبار از طریق public_menu (مثل crypto news)
            news_list = await public_menu.fetch_ai_news()
            message = public_menu.format_ai_news_message(news_list)
            
            # ویرایش پیام با نتایج
            await loading_message.edit_text(
                message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"خطا در دریافت اخبار AI: {e}")
            error_message = f"❌ خطا در دریافت اخبار:\n{str(e)}"
            await loading_message.edit_text(error_message)
        
        return
    
    elif message_text == "📷 استخراج متن از عکس":
        bot_logger.log_user_action(user.id, "OCR_REQUEST", "درخواست استخراج متن از عکس")
        
        # نمایش راهنمای OCR
        await update.message.reply_text(
            ocr_handler.get_usage_info(),
            parse_mode='Markdown',
            disable_web_page_preview=False
        )
        
        # اضافه کردن reply keyboard با دکمه خروج
        exit_keyboard = ReplyKeyboardMarkup(
            [["🔙 بازگشت به منوی AI"]],
            resize_keyboard=True
        )
        await update.message.reply_text(
            "📷 لطفاً عکس مورد نظر را ارسال کنید یا روی دکمه زیر کلیک کنید:",
            reply_markup=exit_keyboard
        )
        
        return
    
    if message_text == "🔙 بازگشت به منوی AI":
        # پاک کردن حافظه چت و غیرفعال کردن حالت چت
        try:
            # end_chat هم state رو false می‌کنه هم تاریخچه رو پاک می‌کنه
            ai_chat_state.end_chat(user.id)
            bot_logger.log_user_action(user.id, "AI_CHAT_ENDED", "خروج از حالت چت و پاک کردن حافظه")
            
            await update.message.reply_text(
                "🤖 **منوی هوش مصنوعی**\n\n✅ چت پایان یافت و حافظه پاک شد",
                parse_mode='Markdown',
                reply_markup=get_ai_menu_markup()
            )
        except Exception as e:
            logger.error(f"خطا در پاک کردن حافظه چت: {e}")
            await update.message.reply_text(
                "🤖 **منوی هوش مصنوعی**",
                parse_mode='Markdown',
                reply_markup=get_ai_menu_markup()
            )
        return

# Handler برای پردازش عکس (AI Vision یا OCR)
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر اصلی برای پردازش تصاویر - AI Vision یا OCR"""
    user = update.effective_user
    
    # چک کردن دسترسی
    if not await check_user_access(user.id):
        if db_manager.is_user_blocked(user.id):
            await update.message.reply_text("🚫 شما از استفاده از این ربات محروم شده‌اید.")
        else:
            await update.message.reply_text("🔧 ربات در حال تعمیر است. لطفاً بعداً تلاش کنید.")
        return
    
    # چک اسپم
    is_spam = await check_spam_and_handle(update, context)
    if is_spam:
        return
    
    # به‌روزرسانی فعالیت
    db_manager.update_user_activity(user.id)
    
    # اگر کاربر در حالت چت AI است، عکس را به AI بفرست
    if ai_chat_state.is_in_chat(user.id):
        await ai_vision_handler(update, context)
    else:
        # در غیر این صورت، OCR انجام بده
        await ocr_image_handler(update, context)

# Handler برای ارسال عکس به AI (Vision)
async def ai_vision_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش تصویر با AI Vision در حالت چت"""
    user = update.effective_user
    
    # دریافت caption (اگر کاربر با عکس متن فرستاده)
    caption = update.message.caption or "این عکس چیست؟ توضیح بده."
    
    try:
        # نمایش پیام loading
        loading_message = await update.message.reply_text("🤖 در حال تحلیل تصویر...")
        
        # دریافت بهترین کیفیت تصویر
        photo = update.message.photo[-1]
        
        # دانلود تصویر
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        image_data = bytes(image_bytes)
        
        # تبدیل به base64
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # ارسال به AI
        bot_logger.log_user_action(user.id, "AI_VISION", f"تحلیل تصویر: {caption[:30]}...")
        
        result = await gemini_chat.send_vision_message(user.id, caption, image_base64)
        
        # حذف پیام loading
        await loading_message.delete()
        
        if result.get('success'):
            response = result['response']
            
            # ارسال پاسخ
            await update.message.reply_text(
                f"🤖 **پاسخ AI:**\n\n{response}",
                parse_mode='Markdown'
            )
            
            bot_logger.log_user_action(
                user.id, 
                "AI_VISION_SUCCESS", 
                f"تصویر تحلیل شد. توکن: {result.get('tokens_used', 0)}"
            )
        else:
            error_msg = result.get('error', 'خطای ناشناخته')
            await update.message.reply_text(
                f"❌ خطا در تحلیل تصویر:\n{error_msg}\n\n💡 می‌توانید دوباره تلاش کنید."
            )
    
    except Exception as e:
        logger.error(f"خطا در AI vision: {e}")
        if 'loading_message' in locals():
            await loading_message.delete()
        await update.message.reply_text(
            f"❌ خطا در پردازش تصویر:\n{str(e)}\n\n💡 لطفاً دوباره تلاش کنید."
        )

# OCR Handler for Image Processing  
async def ocr_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر پردازش تصاویر برای OCR"""
    user = update.effective_user
    
    # بررسی اینکه آیا تصویر است
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return
    
    try:
        # نمایش پیام loading
        loading_message = await update.message.reply_text("🔄 در حال پردازش تصویر...")
        
        # دریافت بهترین کیفیت تصویر
        photo = update.message.photo[-1]
        
        # دانلود تصویر
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        image_data = bytes(image_bytes)
        
        # پردازش OCR
        result = ocr_handler.extract_text_from_image(image_data)
        
        # حذف پیام loading
        await loading_message.delete()
        
        # نمایش نتیجه
        formatted_result = ocr_handler.format_ocr_result(result)
        await update.message.reply_text(
            formatted_result,
            parse_mode='Markdown'
        )
        
        # لاگ کردن عملیات
        bot_logger.log_user_action(user.id, "OCR_PROCESSED", "تصویر پردازش شد")
        
    except Exception as e:
        await loading_message.delete()
        logger.error(f"خطا در پردازش OCR: {e}")
        await update.message.reply_text(
            "❌ متاسفانه در پردازش تصویر خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )
    
    return
    
    # برای پیام‌های ناشناخته، جواب نده
    # فقط فعالیت کاربر به‌روزرسانی شده و لاگ ثبت می‌شود
    pass

# Handler برای broadcast (پیام همگانی)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند پیام همگانی"""
    user = update.effective_user
    
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید.")
        return ConversationHandler.END
    
    # دریافت آمار کاربران
    active_users_today = len(db_manager.get_active_users_ids())  # فعال امروز
    all_unblocked = len(db_manager.get_all_unblocked_users_ids())  # همه غیربلاک
    
    await update.message.reply_text(
        f"📢 **ارسال پیام همگانی**\n\n"
        f"👥 کاربران فعال امروز: {active_users_today}\n"
        f"📊 کل کاربران غیربلاک: {all_unblocked}\n\n"
        f"لطفاً پیام مورد نظر خود را بفرستید:\n"
        f"(برای لغو /cancel بفرستید)"
    )
    return BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت پیام و ارسال همگانی"""
    user = update.effective_user
    message_text = update.message.text
    
    if message_text.startswith('/cancel'):
        await update.message.reply_text("❌ پیام همگانی لغو شد.")
        return ConversationHandler.END
    
    # دریافت لیست همه کاربران غیربلاک برای ارسال
    all_users = db_manager.get_all_unblocked_users_ids()
    active_today = len(db_manager.get_active_users_ids())
    
    if not all_users:
        await update.message.reply_text("❌ هیچ کاربر غیربلاکی یافت نشد.")
        return ConversationHandler.END
    
    # تأیید ارسال
    confirm_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید و ارسال", callback_data=f"broadcast_confirm:{len(all_users)}"),
            InlineKeyboardButton("❌ لغو", callback_data="broadcast_cancel")
        ]
    ])
    
    # محدود کردن پیش‌نمایش به 200 کاراکتر
    preview_text = message_text[:200] + ('...' if len(message_text) > 200 else '')
    
    preview_message = f"""
📢 **پیش‌نمایش پیام همگانی**

**👥 تعداد گیرندگان:** {len(all_users)} کاربر
**✨ فعال امروز:** {active_today} کاربر

**📄 متن پیام:**
{preview_text}

آیا می‌خواهید این پیام را ارسال کنید؟
    """
    
    # ذخیره پیام در context برای استفاده بعدی
    context.user_data['broadcast_message'] = message_text
    
    try:
        await update.message.reply_text(
            preview_message, 
            reply_markup=confirm_keyboard,
            parse_mode='Markdown'
        )
    except Exception as e:
        # اگر markdown مشکل داشت، بدون markdown ارسال کن
        logger.warning(f"خطا در ارسال با Markdown: {e}")
        await update.message.reply_text(
            preview_message, 
            reply_markup=confirm_keyboard
        )
    return ConversationHandler.END

# Handler برای callback های broadcast
async def broadcast_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت callback های پیام همگانی"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id != ADMIN_USER_ID:
        await query.edit_message_text("❌ شما دسترسی به این عملیات ندارید.")
        return
    
    if query.data.startswith("broadcast_confirm:"):
        user_count = int(query.data.split(":")[1])
        message_text = context.user_data.get('broadcast_message')
        
        if not message_text:
            await query.edit_message_text("❌ پیام یافت نشد. لطفاً دوباره تلاش کنید.")
            return
        
        await query.edit_message_text(
            f"📤 **در حال ارسال پیام همگانی...**\n\n"
            f"👥 تعداد گیرندگان: {user_count}\n"
            f"⏳ لطفاً صبر کنید..."
        )
        
        # ارسال پیام همگانی
        success_count, fail_count = await send_broadcast_message(context.bot, message_text)
        
        # گزارش نتیجه
        result_message = f"""
📊 **گزارش پیام همگانی**

✅ **ارسال موفق:** {success_count} کاربر
❌ **ارسال ناموفق:** {fail_count} کاربر
📱 **کل تلاش:** {success_count + fail_count} کاربر

📝 **متن ارسال شده:**
{message_text[:100]}{'...' if len(message_text) > 100 else ''}
        """
        
        # لاگ عملیات
        bot_logger.log_admin_action(
            user_id, 
            "BROADCAST_SENT", 
            target=f"{success_count + fail_count} کاربر",
            details=f"موفق: {success_count}, ناموفق: {fail_count}"
        )
        
        await query.edit_message_text(result_message, parse_mode='Markdown')
        
        # پاک کردن پیام از context
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']
    
    elif query.data == "broadcast_cancel":
        await query.edit_message_text("❌ ارسال پیام همگانی لغو شد.")
        
        # پاک کردن پیام از context
        if 'broadcast_message' in context.user_data:
            del context.user_data['broadcast_message']

async def send_broadcast_message(bot, message_text: str) -> tuple:
    """ارسال پیام همگانی به تمام کاربران غیربلاک"""
    all_users = db_manager.get_all_unblocked_users_ids()
    success_count = 0
    fail_count = 0
    blocked_by_user_count = 0
    
    for user_id in all_users:
        try:
            # سعی می‌کنیم با Markdown ارسال کنیم
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **پیام همگانی ادمین**\n\n{message_text}",
                    parse_mode='Markdown'
                )
            except Exception as markdown_error:
                # اگر Markdown مشکل داشت، بدون formatting ارسال کن
                if "can't parse" in str(markdown_error).lower():
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"📢 پیام همگانی ادمین\n\n{message_text}"
                    )
                else:
                    raise  # اگر خطای دیگه‌ای بود، throw کن
            
            success_count += 1
            
            # تأخیر برای جلوگیری از Rate Limit
            await asyncio.sleep(0.05)  # 50ms
            
        except Exception as e:
            fail_count += 1
            error_msg = str(e).lower()
            
            # لاگ خطا
            logger.warning(f"خطا در ارسال پیام به {user_id}: {e}")
            
            # اگر کاربر ربات رو بلاک کرده، فقط لاگ می‌کنیم (نباید او رو بلاک کنیم!)
            if "blocked by the user" in error_msg or "bot was blocked" in error_msg:
                blocked_by_user_count += 1
                logger.info(f"کاربر {user_id} ربات را بلاک کرده است")
            # اگر chat یافت نشد یا user دیگه وجود نداره
            elif "chat not found" in error_msg or "user not found" in error_msg:
                logger.info(f"کاربر {user_id} یافت نشد (احتمالاً حساب حذف شده)")
    
    # لاگ خلاصه
    if blocked_by_user_count > 0:
        logger.info(f"📊 تعداد کاربرانی که ربات را بلاک کرده‌اند: {blocked_by_user_count}")
    
    return success_count, fail_count

# Handler برای خطاها
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاها"""
    error_msg = str(context.error)
    logger.warning('Update "%s" caused error "%s"', update, error_msg)
    
    # بررسی اگر خطا مربوط به conflict است
    if "Conflict" in error_msg and "terminated by other getUpdates request" in error_msg:
        logger.error("🚨 خطای Conflict شناسایی شد - احتمال وجود instance دیگر!")
        logger.error("💡 برای حل: در Koyeb همه deployments قدیمی رو حذف کن")
        # در صورت conflict، پیام خطا به کاربر ارسال نمیکنیم چون ممکنه اوضاع بدتر شه
        return
    
    # لاگ خطا پیشرفته
    user_id = None
    if update and update.effective_user:
        user_id = update.effective_user.id
    
    bot_logger.log_error(f"خطا در پردازش update: {error_msg}", context.error)
    
    # ارسال پیام خطا به کاربر (در صورت امکان)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.\n"
                "در صورت تکرار مشکل، با ادمین تماس بگیرید."
            )
        except Exception:
            pass  # اگر نتوانست پیام خطا ارسال کند، نادیده بگیر

# Background Tasks برای Anti-Spam System
async def auto_unblock_task():
    """تسک پس‌زمینه برای آنبلاک خودکار کاربرها"""
    while True:
        try:
            # هر 1 دقیقه چک کن
            await asyncio.sleep(60)
            
            # آنبلاک کاربرهایی که زمانشان تموم شده
            unblocked_count = db_manager.auto_unblock_expired_users()
            
            # فقط اگر کاربری آنبلاک شد، لاگ کن
            if unblocked_count > 0:
                bot_logger.log_system_event(
                    "AUTO_UNBLOCK",
                    f"{unblocked_count} کاربر به صورت خودکار آنبلاک شدند"
                )
        except Exception as e:
            logger.error(f"❌ خطا در auto_unblock_task: {e}")

async def cleanup_tracking_task():
    """تسک پس‌زمینه برای پاک‌سازی رکوردهای قدیمی tracking"""
    while True:
        try:
            # هر 1 ساعت یکبار پاک‌سازی کن
            await asyncio.sleep(3600)
            
            # پاک کردن رکوردهای بیش از 24 ساعته
            db_manager.cleanup_old_message_tracking(hours=24)
            
        except Exception as e:
            logger.error(f"❌ خطا در cleanup_tracking_task: {e}")

async def run_database_migrations():
    """اجرای migrationهای دیتابیس در زمان شروع ربات"""
    try:
        logger.info("🔧 چک کردن migrationهای دیتابیس...")
        
        # Migration: اضافه کردن فیلد news_subscription_enabled
        conn = db_manager.get_connection()
        if conn:
            cursor = conn.cursor()
            
            # بررسی وجود فیلد
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='news_subscription_enabled'
            """)
            
            result = cursor.fetchone()
            
            if not result:
                logger.info("🔧 اضافه کردن فیلد news_subscription_enabled...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN news_subscription_enabled BOOLEAN DEFAULT FALSE
                """)
                conn.commit()
                logger.info("✅ فیلد news_subscription_enabled با موفقیت اضافه شد")
            else:
                # چک کردن نوع فیلد
                cursor.execute("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='news_subscription_enabled'
                """)
                data_type_result = cursor.fetchone()
                
                if data_type_result and data_type_result[0] == 'integer':
                    logger.info("🔧 تغییر نوع فیلد news_subscription_enabled از INTEGER به BOOLEAN...")
                    # تغییر نوع فیلد
                    cursor.execute("""
                        ALTER TABLE users 
                        ALTER COLUMN news_subscription_enabled TYPE BOOLEAN 
                        USING CASE WHEN news_subscription_enabled = 1 THEN TRUE ELSE FALSE END
                    """)
                    conn.commit()
                    logger.info("✅ نوع فیلد با موفقیت تغییر یافت")
                else:
                    logger.info("✅ فیلد news_subscription_enabled قبلاً با نوع صحیح وجود دارد")
            
            cursor.close()
            db_manager.return_connection(conn)
            
    except Exception as e:
        logger.error(f"❌ خطا در migration: {e}")

async def main() -> None:
    """تابع اصلی برای راه‌اندازی ربات"""
    logger.info("🚀 شروع ربات تلگرام پیشرفته...")
    logger.info(f"🔑 BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
    logger.info(f"👤 ADMIN_USER_ID: {ADMIN_USER_ID}")
    logger.info(f"🌍 ENVIRONMENT: {ENVIRONMENT}")
    
    # اجرای migrationهای دیتابیس
    await run_database_migrations()
    
    # لاگ شروع سیستم
    bot_logger.log_system_event("BOT_STARTED", f"ربات در زمان {datetime.datetime.now()} شروع شد")
    
    # تاخیر کوتاه برای جلوگیری از مشکل race condition
    import time
    time.sleep(2)
    logger.info("⏳ آماده‌سازی اتصال...")
    
    # ایجاد Application با token ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # مقداردهی application (async)
    await application.initialize()

    # Handler های دستورات اصلی
    application.add_handler(CommandHandler("start", start))
    # Help command removed - not needed
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("status", status_command))
    # Signal command handler removed
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Handler برای پنل ادمین (callback queries)
    application.add_handler(CallbackQueryHandler(admin_panel.handle_admin_callback, pattern="^(admin_|sys_|users_|user_|logs_)"))
    
    # Handler برای منوی عمومی (callback queries)  
    application.add_handler(CallbackQueryHandler(public_menu.handle_public_callback, pattern="^(public_|crypto_)"))

    # Handler برای لیگ‌های یادآوری ورزشی
    application.add_handler(CallbackQueryHandler(handle_sports_league_callback, pattern=r"^sports_reminder_(league|team|back|cancel|remove)"))
    
    # Handler برای اشتراک اخبار (callback queries)
    application.add_handler(CallbackQueryHandler(news_subscription_callback, pattern="^news_sub_"))
    
    # Handler برای broadcast callbacks
    application.add_handler(CallbackQueryHandler(broadcast_callback_handler, pattern="^broadcast_"))
    
    # ConversationHandler برای پیام همگانی
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    application.add_handler(broadcast_conv_handler)
    
    # ConversationHandler برای تحلیل TradingView
    tradingview_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📈 تحلیل TradingView$"), tradingview_analysis_start)],
        states={
            TRADINGVIEW_ANALYSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tradingview_analysis_process)],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )
    application.add_handler(tradingview_conv_handler)
    
    # Handler برای پیام‌های ناشناخته (راهنمایی ساده)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))
    
    # Photo Handler (AI Vision or OCR)
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    # Handler برای خطاها
    application.add_error_handler(error_handler)

    # نمایش اطلاعات شروع
    stats = db_manager.get_user_stats()
    logger.info(f"✅ ربات راه‌اندازی شد!")
    logger.info(f"📊 آمار: {stats['total']} کاربر، {stats['active']} فعال")
    logger.info(f"👨‍💼 ادمین: {ADMIN_USER_ID}")
    logger.info(f"🔗 آماده دریافت پیام...")
    
    # شروع AsyncIO HTTP server برای health check و webhook
    import json
    from aiohttp import web, ClientSession
    import threading
    import weakref
    
    async def health_check(request):
        """Health check endpoint"""
        health_data = {
            "status": "healthy",
            "service": "telegram-bot", 
            "timestamp": datetime.datetime.now().isoformat(),
            "uptime": "running",
            "mode": "webhook" if os.getenv('USE_WEBHOOK') == 'true' else "polling"
        }
        return web.json_response(health_data)
    
    async def ping_endpoint(request):
        """Simple ping endpoint"""
        return web.Response(text='pong')
    
    async def wake_endpoint(request):
        """Wake endpoint"""
        wake_data = {
            "status": "awake",
            "message": "Service is now active",
            "timestamp": datetime.datetime.now().isoformat()
        }
        return web.json_response(wake_data)
    
    # ذخیره reference به application برای webhook
    telegram_app_ref = weakref.ref(application)
    
    async def telegram_webhook(request):
        """Webhook endpoint برای دریافت updates تلگرام"""
        try:
            app = telegram_app_ref()
            if app is None:
                return web.Response(status=500, text="Telegram app not available")
                
            # دریافت update از تلگرام
            update_data = await request.json()
            update = Update.de_json(update_data, app.bot)
            
            # پردازش update
            await app.process_update(update)
            
            return web.Response(status=200, text="OK")
        except Exception as e:
            logger.error(f"❌ خطا در webhook: {e}")
            return web.Response(status=500, text="Error")
    
    async def start_aiohttp_server():
        """راه‌اندازی AsyncIO HTTP server"""
        app_web = web.Application()
        
        # اضافه کردن routes
        app_web.router.add_get('/health', health_check)
        app_web.router.add_get('/', health_check)
        app_web.router.add_get('/ping', ping_endpoint)
        app_web.router.add_get('/wake', wake_endpoint)
        
        # Webhook endpoint (فقط اگر فعال باشد)
        if os.getenv('USE_WEBHOOK') == 'true':
            app_web.router.add_post('/webhook', telegram_webhook)
            logger.info("🔗 Webhook endpoint فعال شد: /webhook")
        
        # شروع server
        port = int(os.getenv('PORT', 8000))
        runner = web.AppRunner(app_web)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🏥 AsyncIO HTTP server در پورت {port}")
        return runner
    
    # Async Keep-Alive Mechanism 
    async def async_keep_alive():
        """AsyncIO keep-alive mechanism - بهینه شده برای کاهش بار"""
        app_url = os.getenv('KOYEB_PUBLIC_DOMAIN')
        if not app_url:
            return
            
        if not app_url.startswith('http'):
            app_url = f"https://{app_url}"
        
        async with ClientSession() as session:
            ping_count = 0
            while True:
                try:
                    await asyncio.sleep(600)  # هر 10 دقیقه (کاهش از 4 دقیقه)
                    async with session.get(f"{app_url}/ping", timeout=10) as response:
                        if response.status == 200:
                            ping_count += 1
                            # فقط هر 6 بار (یعنی هر 1 ساعت) لاگ کن
                            if ping_count % 6 == 0:
                                logger.info(f"✅ Keep-alive فعال است ({ping_count} ping موفق)")
                        else:
                            logger.warning(f"⚠️ Keep-alive ناموفق: {response.status}")
                except Exception as e:
                    logger.error(f"❌ خطا در keep-alive: {e}")
    
    # شروع HTTP server در event loop
    def start_http_in_thread():
        """شروع HTTP server در thread جداگانه"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_server():
            # شروع HTTP server
            runner = await start_aiohttp_server()
            
            # شروع keep-alive اگر DOMAIN تنظیم شده
            if os.getenv('KOYEB_PUBLIC_DOMAIN'):
                asyncio.create_task(async_keep_alive())
                logger.info("🏓 Async keep-alive فعال شد")
            
            # نگهداری server
            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                await runner.cleanup()
        
        loop.run_until_complete(run_server())
    
    # شروع HTTP server در thread جداگانه
    http_thread = threading.Thread(target=start_http_in_thread, daemon=True)
    http_thread.start()
    
    # 🚨 شروع Background Tasks برای Anti-Spam System
    logger.info("🧹 شروع Background Tasks...")
    asyncio.create_task(auto_unblock_task())
    asyncio.create_task(cleanup_tracking_task())
    logger.info("✅ Background Tasks فعال شدند (auto-unblock, cleanup)")
    
    # 📆 راه‌اندازی Scheduler برای ارسال خودکار اخبار
    logger.info("🕒 راه‌اندازی Scheduler برای ارسال خودکار اخبار...")
    
    # ایجاد scheduler
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Tehran'))
    
    # اضافه کردن job برای صبح (8:00)
    scheduler.add_job(
        send_scheduled_news,
        trigger=CronTrigger(hour=8, minute=0, timezone='Asia/Tehran'),
        args=[application],
        id='morning_news',
        name='ارسال اخبار صبح',
        replace_existing=True
    )
    
    # اضافه کردن job برای ظهر (14:00)
    scheduler.add_job(
        send_scheduled_news,
        trigger=CronTrigger(hour=14, minute=0, timezone='Asia/Tehran'),
        args=[application],
        id='afternoon_news',
        name='ارسال اخبار ظهر',
        replace_existing=True
    )
    
    # اضافه کردن job برای شب (20:00)
    scheduler.add_job(
        send_scheduled_news,
        trigger=CronTrigger(hour=20, minute=0, timezone='Asia/Tehran'),
        args=[application],
        id='evening_news',
        name='ارسال اخبار شب',
        replace_existing=True
    )

    # اضافه کردن job هفتگی برای به‌روزرسانی یادآوری بازی‌ها (جمعه ساعت 02:00 به وقت تهران)
    scheduler.add_job(
        refresh_weekly_sports_reminders,
        trigger=CronTrigger(day_of_week='fri', hour=2, minute=0, timezone='Asia/Tehran'),
        args=[application],
        name="weekly_sports_reminder_refresh"
    )

    # اضافه کردن job روزانه برای به‌روزرسانی یادآوری تیم‌ها
    scheduler.add_job(
        refresh_daily_sports_reminders,
        trigger=CronTrigger(hour=3, minute=0, timezone='Asia/Tehran'),
        args=[application],
        name="daily_sports_reminder_refresh"
    )

    # اضافه کردن job دوره‌ای برای ارسال یادآوری‌های رسیده (هر 5 دقیقه)
    scheduler.add_job(
        process_due_sports_reminders,
        trigger=CronTrigger(minute='*/5', timezone='Asia/Tehran'),
        args=[application],
        id='sports_reminder_dispatch',
        name='ارسال یادآوری‌های ورزشی',
        replace_existing=True
    )
    
    # شروع scheduler
    scheduler.start()
    logger.info("✅ Scheduler فعال شد - اخبار در ساعت‌های 8:00, 14:00, 20:00 (وقت ایران) ارسال خواهد شد")
    
    # انتخاب بین Webhook و Polling
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    webhook_url = os.getenv('KOYEB_PUBLIC_DOMAIN')
    
    if use_webhook and webhook_url:
        logger.info("🔗 تنظیم Webhook Mode...")
        
        if not webhook_url.startswith('http'):
            webhook_url = f"https://{webhook_url}"
        
        # اجرای ربات با Webhook
        try:
            logger.info(f"📡 تنظیم webhook: {webhook_url}/webhook")
            
            # Set webhook
            await application.bot.set_webhook(
                url=f"{webhook_url}/webhook",
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
            logger.info("✅ Webhook تنظیم شد!")
            logger.info("🏃‍♂️ سرویس در حالت Webhook اجرا می‌شود...")
            logger.info("💡 Health check در /health فعال است")
            
            # نگهداری سرویس زنده (Koyeb خودش /health را می‌زند)
            heartbeat_count = 0
            while True:
                await asyncio.sleep(1800)  # هر 30 دقیقه (کاهش از 30 ثانیه)
                heartbeat_count += 1
                logger.info(f"💚 Webhook Mode: فعال است ({heartbeat_count * 30} دقیقه uptime)")
                
        except KeyboardInterrupt:
            logger.info("🛑 ربات متوقف شد")
            await application.bot.delete_webhook()
        except Exception as e:
            logger.error(f"❌ خطا در webhook mode: {e}")
            await application.bot.delete_webhook()
            bot_logger.log_error("خطا در webhook mode", e)
    else:
        # اجرای ربات با Polling (حالت عادی)
        try:
            logger.info("📡 شروع polling...")
            logger.info("🔍 بررسی اتصال Telegram...")
            
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=1.0,
                timeout=10
            )
        except KeyboardInterrupt:
            logger.info("🛑 ربات متوقف شد")
            bot_logger.log_system_event("BOT_STOPPED", "ربات توسط کاربر متوقف شد")
        except Exception as e:
            error_msg = str(e)
            if "Conflict" in error_msg and "terminated by other getUpdates request" in error_msg:
                logger.error("🚨 خطای Conflict در polling!")
                logger.error("💡 راه حل: در Koyeb تمام deployments قدیمی رو حذف کن و فقط یکی بذار")
                logger.error("📍 یا اگر ربات روی سیستم محلی اجرا میکنی، اونو متوقف کن")
            else:
                logger.error(f"❌ خطا در اجرای ربات: {e}")
            bot_logger.log_error("خطا در اجرای ربات", e)

if __name__ == "__main__":
    asyncio.run(main())