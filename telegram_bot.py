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
import os
import re
from dotenv import load_dotenv
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (Application, CommandHandler, ContextTypes, 
                          MessageHandler, filters, CallbackQueryHandler, ConversationHandler)

# Load environment variables
load_dotenv()

# Choose database based on environment
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
    from database_postgres import PostgreSQLManager as DatabaseManager, DatabaseLogger
else:
    from database import DatabaseManager, DatabaseLogger

from admin_panel import AdminPanel
from public_menu import PublicMenuManager
from logger_system import bot_logger
from keyboards import get_main_menu_markup, get_ai_menu_markup, get_crypto_menu_markup
from ai_news import get_ai_news

# Optional imports - TradingView Analysis
try:
    from tradingview_analysis import TradingViewAnalysisFetcher
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
logging.getLogger("httpx").setLevel(logging.WARNING)

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

# Initialize TradingView fetcher if available
if TRADINGVIEW_AVAILABLE:
    tradingview_fetcher = TradingViewAnalysisFetcher()
else:
    tradingview_fetcher = None

# متغیرهای مکالمه
(BROADCAST_MESSAGE, USER_SEARCH, USER_ACTION, TRADINGVIEW_ANALYSIS, MAIN_MENU, AI_MENU, CRYPTO_MENU) = range(7)

# بررسی دسترسی کاربر
async def check_user_access(user_id: int) -> bool:
    """بررسی دسترسی کاربر به ربات"""
    # ادمین همیشه دسترسی دارد
    if user_id == ADMIN_USER_ID:
        return True
    
    # بررسی فعال بودن ربات
    if not db_manager.is_bot_enabled():
        return False
    
    # بررسی بلاک بودن کاربر
    if db_manager.is_user_blocked(user_id):
        return False
    
    return True

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

از دکمه زیر برای مشاهده قیمت‌های لحظه‌ای ارزهای دیجیتال، تتر و دلار استفاده کنید 💰
    """
    
    # ایجاد کیبورد ساده
    keyboard = [
        [KeyboardButton("💰 ارزهای دیجیتال")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    # نمایش پیام خوش آمدگویی
    await update.message.reply_html(
        welcome_message,
        reply_markup=reply_markup
    )

# Handler برای دستور /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش راهنما"""
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        return
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    help_text = """
📚 **راهنمای کامل ربات**

**🔹 دستورات عمومی:**
/start - شروع مجدد ربات
/help - نمایش این راهنما
/status - وضعیت ربات و اطلاعات شما

**🔹 دستورات مدیریت:**
/admin - پنل مدیریت کامل (فقط ادمین)

**🔹 قابلیت‌های ربات:**
✅ پردازش پیام‌های متنی
✅ سیستم مدیریت کاربران
✅ آمارگیری و گزارش‌گیری
✅ پنل ادمین با امکانات کامل
✅ سیستم لاگ و رصد فعالیت‌ها
✅ قابلیت پیام همگانی

**🔹 نحوه استفاده:**
• هر پیام متنی بفرستید تا پردازش شود
• از دستورات بالا برای عملکردهای خاص استفاده کنید
• ادمین از طریق /admin به تمام امکانات دسترسی دارد

**💡 نکته:** تمام فعالیت‌های شما ثبت و آمارگیری می‌شود.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

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
🤖 *هوش مصنوعی:* آخرین اخبار و پیشرفت‌های AI
📊 *پورتفولیو:* مدیریت سرمایه‌گذاری‌ها
📈 *تحلیل:* تحلیل تکنیکال ارزها
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
    
    status_text = f"""
📊 **وضعیت ربات و کاربر**

**🤖 وضعیت ربات:**
• ربات: {bot_status}
• مدت اجرا: {datetime.datetime.now() - admin_panel.bot_start_time}
• کل کاربران: {stats['total']}

**👤 اطلاعات شما:{admin_badge}**
• نام: {user.full_name}
• نام کاربری: @{user.username or 'ندارد'}
• شناسه: `{user.id}`
• وضعیت: {user_status}

**📈 آمار فعالیت شما:**
• تاریخ عضویت: {join_date.strftime('%Y/%m/%d %H:%M')}
• آخرین فعالیت: {last_activity.strftime('%Y/%m/%d %H:%M')}
• روزهای عضویت: {days_since_join}
• تعداد پیام‌ها: {user_data['message_count'] if user_data else 0}

**🌐 اطلاعات سرور:**
• زمان سرور: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
• وضعیت اتصال: ✅ متصل
    """
    await update.message.reply_text(status_text, parse_mode='Markdown')

# Handler برای دستور /admin (فقط برای ادمین)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پنل مدیریت پیشرفته - فقط برای ادمین"""
    user = update.effective_user
    
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید.")
        return
    
    # لاگ دسترسی ادمین
    bot_logger.log_admin_action(user.id, "ADMIN_PANEL_ACCESS")
    
    welcome_text = f"""
🔧 **پنل مدیریت ربات**

خوش آمدید {user.first_name}! 👨‍💼

این پنل امکانات کاملی برای مدیریت ربات فراهم می‌کند:

🖥️ **سیستم:** مدیریت منابع و وضعیت
👥 **کاربران:** مدیریت و آمارگیری کاربران  
📊 **آمار:** گزارش‌های تفصیلی
📋 **لاگ‌ها:** رصد فعالیت‌ها
📢 **پیام همگانی:** ارسال به همه کاربران
⚙️ **تنظیمات:** پیکربندی ربات

یک بخش را انتخاب کنید:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=admin_panel.create_main_menu_keyboard(),
        parse_mode='Markdown'
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
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    # لاگ پیام
    db_logger.log_user_action(user.id, "MESSAGE_SENT", f"پیام ارسال شد: {update.message.text[:50]}...")
    
    message_text = update.message.text
    user_data = db_manager.get_user(user.id)
    
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
            [KeyboardButton("📊 قیمت‌های لحظه‌ای")],
            [KeyboardButton("📰 اخبار کریپتو")],
            [KeyboardButton("📈 تحلیل TradingView")],
            [KeyboardButton("🔙 بازگشت به منوی اصلی")]
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
            
            # ویرایش پیام با نتایج
            await loading_message.edit_text(message, parse_mode='Markdown')
            
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
    
    elif message_text == "🔙 بازگشت به منوی اصلی":
        # بازگشت به منوی اصلی
        welcome_message = """
سلام! 👋

به ربات خوش آمدید!

از دکمه زیر برای مشاهده قیمت‌های لحظه‌ای ارزهای دیجیتال، تتر و دلار استفاده کنید 💰
        """
        
        # ایجاد کیبورد ساده
        keyboard = [
            [KeyboardButton("💰 ارزهای دیجیتال")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup
        )
        return
    
    
    # برای پیام‌های ناشناخته، راهنمایی ساده
    help_message = """
ℹ️ از دکمه‌های منو استفاده کنید یا یکی از دستورات زیر را امتحان کنید:

🔹 /start - شروع مجدد
🔹 /menu - نمایش منو
🔹 /help - راهنما
🔹 /status - وضعیت ربات
    """

    
    await update.message.reply_text(help_message)

# Handler برای broadcast (پیام همگانی)
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند پیام همگانی"""
    user = update.effective_user
    
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("❌ شما دسترسی به این دستور ندارید.")
        return ConversationHandler.END
    
    active_users = len(db_manager.get_active_users_ids())
    
    await update.message.reply_text(
        f"📢 **ارسال پیام همگانی**\n\n"
        f"👥 تعداد کاربران فعال: {active_users}\n\n"
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
    
    # دریافت لیست کاربران فعال
    active_users = db_manager.get_active_users_ids()
    
    if not active_users:
        await update.message.reply_text("❌ هیچ کاربر فعالی یافت نشد.")
        return ConversationHandler.END
    
    # تأیید ارسال
    confirm_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید و ارسال", callback_data=f"broadcast_confirm:{len(active_users)}"),
            InlineKeyboardButton("❌ لغو", callback_data="broadcast_cancel")
        ]
    ])
    
    preview_message = f"""
📢 **پیش‌نمایش پیام همگانی**

**👥 تعداد گیرندگان:** {len(active_users)} کاربر

**📄 متن پیام:**
{message_text}

آیا می‌خواهید این پیام را ارسال کنید؟
    """
    
    # ذخیره پیام در context برای استفاده بعدی
    context.user_data['broadcast_message'] = message_text
    
    await update.message.reply_text(
        preview_message, 
        reply_markup=confirm_keyboard,
        parse_mode='Markdown'
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
    """ارسال پیام همگانی به تمام کاربران فعال"""
    active_users = db_manager.get_active_users_ids()
    success_count = 0
    fail_count = 0
    
    for user_id in active_users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"📢 **پیام همگانی ادمین**\n\n{message_text}",
                parse_mode='Markdown'
            )
            success_count += 1
            
            # کمی تأخیر برای جلوگیری از Rate Limit
            await asyncio.sleep(0.1)
            
        except Exception as e:
            fail_count += 1
            logger.warning(f"خطا در ارسال پیام به {user_id}: {e}")
            
            # در صورت بلاک شدن از طرف کاربر، او را بلاک کنیم
            if "blocked by the user" in str(e).lower():
                db_manager.block_user(user_id)
    
    return success_count, fail_count

# Handler برای خطاها
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت خطاها"""
    error_msg = str(context.error)
    logger.warning('Update "%s" caused error "%s"', update, error_msg)
    
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

# =========================
# Handler های منوی هوش مصنوعی
# =========================

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مدیریت منوی اصلی"""
    text = update.message.text
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        return ConversationHandler.END
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    if text == "💰 ارزهای دیجیتال":
        bot_logger.log_user_action(user.id, "CRYPTO_MENU_ACCESS", "ورود به بخش ارزهای دیجیتال")
        
        await update.message.reply_text(
            "💰 **بخش ارزهای دیجیتال**\n\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=get_crypto_menu_markup(),
            parse_mode='Markdown'
        )
        return CRYPTO_MENU
    
    elif text == "🤖 هوش مصنوعی":
        bot_logger.log_user_action(user.id, "AI_MENU_ACCESS", "ورود به بخش هوش مصنوعی")
        
        await update.message.reply_text(
            "🤖 **بخش هوش مصنوعی**\n\nبه دنیای AI خوش آمدید! از گزینه‌های زیر استفاده کنید:",
            reply_markup=get_ai_menu_markup(),
            parse_mode='Markdown'
        )
        return AI_MENU
    
    # سایر دکمه‌ها - فعلاً پیام موقت
    elif text in ["📊 پورتفولیو من", "📈 تحلیل تکنیکال", "⚙️ تنظیمات", "📞 پشتیبانی"]:
        await update.message.reply_text(
            f"🚧 بخش **{text}** به زودی راه‌اندازی می‌شود.\n\nدر حال حاضر می‌توانید از بخش‌های ارزهای دیجیتال و هوش مصنوعی استفاده کنید.",
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    # در صورت عدم تطبیق، نمایش منوی اصلی
    await update.message.reply_text(
        "🏠 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_menu_markup(),
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def ai_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مدیریت منوی هوش مصنوعی"""
    text = update.message.text
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        return ConversationHandler.END
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    if text == "📰 اخبار هوش مصنوعی":
        bot_logger.log_user_action(user.id, "AI_NEWS_REQUEST", "درخواست اخبار هوش مصنوعی")
        
        # نمایش پیام "در حال بارگذاری"
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار هوش مصنوعی...")
        
        try:
            # دریافت اخبار
            news_text = await get_ai_news()
            
            # حذف پیام loading
            await loading_message.delete()
            
            # ارسال اخبار
            await update.message.reply_text(
                news_text,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            
        except Exception as e:
            await loading_message.delete()
            logger.error(f"خطا در دریافت اخبار AI: {e}")
            await update.message.reply_text(
                "❌ متاسفانه در دریافت اخبار خطایی رخ داد. لطفاً دوباره تلاش کنید."
            )
        
        return AI_MENU
    
    elif text == "🔙 بازگشت":
        bot_logger.log_user_action(user.id, "BACK_TO_MAIN", "بازگشت به منوی اصلی")
        
        await update.message.reply_text(
            "🏠 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_menu_markup(),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    # در صورت عدم تطبیق، نمایش منوی AI
    await update.message.reply_text(
        "🤖 **بخش هوش مصنوعی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_ai_menu_markup(),
        parse_mode='Markdown'
    )
    return AI_MENU

async def crypto_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مدیریت منوی ارزهای دیجیتال"""
    text = update.message.text
    user = update.effective_user
    
    # بررسی دسترسی
    if not await check_user_access(user.id):
        return ConversationHandler.END
    
    # به‌روزرسانی فعالیت کاربر
    db_manager.update_user_activity(user.id)
    
    if text == "🔙 بازگشت":
        bot_logger.log_user_action(user.id, "BACK_TO_MAIN", "بازگشت به منوی اصلی")
        
        await update.message.reply_text(
            "🏠 **منوی اصلی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_menu_markup(),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    # سایر دکمه‌های crypto - از عملکرد قبلی استفاده می‌شود
    elif text in ["📊 قیمت لحظه‌ای", "📰 اخبار ارز", "🔥 ارزهای ترند", "📈 نمودار قیمت"]:
        # اینجا باید handler های قبلی crypto قرار بگیرد
        # فعلاً پیام موقت
        await update.message.reply_text(
            f"🚧 **{text}** در حال بروزرسانی است.\n\nلطفاً از منوی اصلی استفاده کنید.",
            parse_mode='Markdown'
        )
        return CRYPTO_MENU
    
    # در صورت عدم تطبیق، نمایش منوی crypto
    await update.message.reply_text(
        "💰 **بخش ارزهای دیجیتال**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_crypto_menu_markup(),
        parse_mode='Markdown'
    )
    return CRYPTO_MENU

def main() -> None:
    """تابع اصلی برای راه‌اندازی ربات"""
    logger.info("🚀 شروع ربات تلگرام پیشرفته...")
    logger.info(f"🔑 BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
    logger.info(f"👤 ADMIN_USER_ID: {ADMIN_USER_ID}")
    logger.info(f"🌍 ENVIRONMENT: {ENVIRONMENT}")
    
    # لاگ شروع سیستم
    bot_logger.log_system_event("BOT_STARTED", f"ربات در زمان {datetime.datetime.now()} شروع شد")
    
    # ایجاد Application با token ربات
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler های دستورات اصلی
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Handler برای پنل ادمین (callback queries)
    application.add_handler(CallbackQueryHandler(admin_panel.handle_admin_callback, pattern="^(admin_|sys_|users_|user_|logs_)"))
    
    # Handler برای منوی عمومی (callback queries)  
    application.add_handler(CallbackQueryHandler(public_menu.handle_public_callback, pattern="^(public_|crypto_)"))
    
    # Handler برای broadcast callbacks
    application.add_handler(CallbackQueryHandler(broadcast_callback_handler, pattern="^broadcast_"))
    
    # ConversationHandler برای پیام همگانی
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(broadcast_conv_handler)
    
    # ConversationHandler برای تحلیل TradingView
    tradingview_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📈 تحلیل TradingView$"), tradingview_analysis_start)],
        states={
            TRADINGVIEW_ANALYSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tradingview_analysis_process)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(tradingview_conv_handler)
    
    # ConversationHandler اصلی برای ناوبری بین منوها
    main_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💰 ارزهای دیجیتال$"), main_menu_handler),
            MessageHandler(filters.Regex("^🤖 هوش مصنوعی$"), main_menu_handler),
            MessageHandler(filters.Regex("^📊 پورتفولیو من$"), main_menu_handler),
            MessageHandler(filters.Regex("^📈 تحلیل تکنیکال$"), main_menu_handler),
            MessageHandler(filters.Regex("^⚙️ تنظیمات$"), main_menu_handler),
            MessageHandler(filters.Regex("^📞 پشتیبانی$"), main_menu_handler),
        ],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^💰 ارزهای دیجیتال$"), main_menu_handler),
                MessageHandler(filters.Regex("^🤖 هوش مصنوعی$"), main_menu_handler),
                MessageHandler(filters.Regex("^📊 پورتفولیو من$"), main_menu_handler),
                MessageHandler(filters.Regex("^📈 تحلیل تکنیکال$"), main_menu_handler),
                MessageHandler(filters.Regex("^⚙️ تنظیمات$"), main_menu_handler),
                MessageHandler(filters.Regex("^📞 پشتیبانی$"), main_menu_handler),
            ],
            AI_MENU: [
                MessageHandler(filters.Regex("^📰 اخبار هوش مصنوعی$"), ai_menu_handler),
                MessageHandler(filters.Regex("^🔙 بازگشت$"), ai_menu_handler),
            ],
            CRYPTO_MENU: [
                MessageHandler(filters.Regex("^📊 قیمت لحظه‌ای$"), crypto_menu_handler),
                MessageHandler(filters.Regex("^📰 اخبار ارز$"), crypto_menu_handler),
                MessageHandler(filters.Regex("^🔥 ارزهای ترند$"), crypto_menu_handler),
                MessageHandler(filters.Regex("^📈 نمودار قیمت$"), crypto_menu_handler),
                MessageHandler(filters.Regex("^🔙 بازگشت$"), crypto_menu_handler),
            ],
        },
        fallbacks=[CommandHandler("menu", menu_command)],
    )
    application.add_handler(main_conv_handler)
    
    # Handler برای پیام‌های ناشناخته (راهنمایی ساده)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))
    
    # Handler برای خطاها
    application.add_error_handler(error_handler)

    # نمایش اطلاعات شروع
    stats = db_manager.get_user_stats()
    logger.info(f"✅ ربات راه‌اندازی شد!")
    logger.info(f"📊 آمار: {stats['total']} کاربر، {stats['active']} فعال")
    logger.info(f"👨‍💼 ادمین: {ADMIN_USER_ID}")
    logger.info(f"🔗 آماده دریافت پیام...")
    
    # اجرای ربات تا زمان فشردن Ctrl-C
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("🛑 ربات متوقف شد")
        bot_logger.log_system_event("BOT_STOPPED", "ربات توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات: {e}")
        bot_logger.log_error("خطا در اجرای ربات", e)

if __name__ == "__main__":
    main()