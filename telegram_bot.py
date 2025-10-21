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
import requests
import weakref
from aiohttp import web, ClientSession
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
from keyboards import get_main_menu_markup, get_public_section_markup, get_ai_menu_markup
from ai_news import get_ai_news
# Signal scraper removed - will be re-implemented later

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

# Initialize TradingView fetcher if available
if TRADINGVIEW_AVAILABLE:
    tradingview_fetcher = TradingViewAnalysisFetcher()
else:
    tradingview_fetcher = None

# متغیرهای مکالمه
(BROADCAST_MESSAGE, USER_SEARCH, USER_ACTION, TRADINGVIEW_ANALYSIS) = range(4)

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

# Signal functions removed - will be re-implemented later

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


# Functions for News
async def fetch_coindesk_news():
    """دریافت 5 خبر مهم از سایت CoinDesk"""
    import aiohttp
    from bs4 import BeautifulSoup
    import json
    
    try:
        # URL RSS feed CoinDesk
        coindesk_rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(coindesk_rss_url, timeout=15) as response:
                if response.status == 200:
                    rss_content = await response.text()
                    
                    # پارس کردن RSS
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(rss_content)
                    items = root.findall('.//item')[:5]  # 5 خبر اول
                    
                    news_list = []
                    for item in items:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        description_elem = item.find('description')
                        pub_date_elem = item.find('pubDate')
                        
                        if title_elem is not None and link_elem is not None:
                            # پاک‌سازی عنوان از HTML tags
                            import html
                            title = html.unescape(title_elem.text or '').strip()
                            link = link_elem.text or ''
                            
                            # پاک‌سازی توضیحات
                            description = ''
                            if description_elem is not None and description_elem.text:
                                import re
                                desc_text = html.unescape(description_elem.text)
                                desc_text = re.sub(r'<[^>]+>', '', desc_text)
                                description = desc_text.strip()[:150] + '...' if len(desc_text) > 150 else desc_text.strip()
                            
                            # تاریخ انتشار
                            published = pub_date_elem.text if pub_date_elem is not None else ''
                            
                            news_list.append({
                                'title': title,
                                'link': link,
                                'description': description,
                                'source': 'CoinDesk',
                                'published': published
                            })
                    
                    return news_list
                else:
                    return []
    except Exception as e:
        print(f"خطا در دریافت اخبار CoinDesk: {e}")
        return []


async def fetch_tasnim_news():
    """دریافت آخرین اخبار روز از سایت تسنیم"""
    import aiohttp
    from bs4 import BeautifulSoup
    import json
    
    try:
        # URL RSS feed تسنیم
        tasnim_rss_url = "https://www.tasnimnews.com/fa/rss/feed/0/8/0/%D8%A2%D8%AE%D8%B1%DB%8C%D9%86-%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(tasnim_rss_url, timeout=15) as response:
                if response.status == 200:
                    rss_content = await response.text()
                    
                    # پارس کردن RSS
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(rss_content)
                    items = root.findall('.//item')[:6]  # 6 خبر اول
                    
                    news_list = []
                    for item in items:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        description_elem = item.find('description')
                        pub_date_elem = item.find('pubDate')
                        
                        if title_elem is not None and link_elem is not None:
                            # پاک‌سازی عنوان از HTML tags
                            import html
                            title = html.unescape(title_elem.text or '').strip()
                            link = link_elem.text or ''
                            
                            # پاک‌سازی توضیحات
                            description = ''
                            if description_elem is not None and description_elem.text:
                                import re
                                desc_text = html.unescape(description_elem.text)
                                desc_text = re.sub(r'<[^>]+>', '', desc_text)
                                description = desc_text.strip()[:120] + '...' if len(desc_text) > 120 else desc_text.strip()
                            
                            # تاریخ انتشار
                            published = pub_date_elem.text if pub_date_elem is not None else ''
                            
                            news_list.append({
                                'title': title,
                                'link': link,
                                'description': description,
                                'source': 'تسنیم',
                                'published': published
                            })
                    
                    return news_list
                else:
                    return []
    except Exception as e:
        print(f"خطا در دریافت اخبار تسنیم: {e}")
        return []


def format_crypto_news_message(news_list):
    """فرمت کردن پیام اخبار کریپتو"""
    if not news_list:
        return "❌ خطا در دریافت اخبار کریپتو. لطفاً بعداً امتحان کنید."
    
    message = "📈 *آخرین اخبار کریپتو (CoinDesk)*\n\n"
    
    for i, news in enumerate(news_list, 1):
        title = news['title'][:80] + '...' if len(news['title']) > 80 else news['title']
        description = news.get('description', '')[:100] + '...' if len(news.get('description', '')) > 100 else news.get('description', '')
        
        message += f"📰 *{i}. {title}*\n"
        if description:
            message += f"   {description}\n"
        message += f"   🔗 [ادامه مطلب]({news['link']})\n\n"
    
    message += "🔄 منبع: CoinDesk\n"
    message += "⏰ آخرین به‌روزرسانی: همین الان"
    
    return message


def format_general_news_message(news_list):
    """فرمت کردن پیام اخبار عمومی"""
    if not news_list:
        return "❌ خطا در دریافت اخبار عمومی. لطفاً بعداً امتحان کنید."
    
    message = "📺 *آخرین اخبار روز*\n\n"
    
    for i, news in enumerate(news_list, 1):
        title = news['title'][:70] + '...' if len(news['title']) > 70 else news['title']
        description = news.get('description', '')[:90] + '...' if len(news.get('description', '')) > 90 else news.get('description', '')
        
        message += f"📰 *{i}. {title}*\n"
        if description:
            message += f"   {description}\n"
        message += f"   🔗 [ادامه مطلب]({news['link']})\n\n"
    
    message += "🔄 منبع: تسنیم\n"
    message += "⏰ آخرین به‌روزرسانی: همین الان"
    
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
    
    status_text = f"""
📊 **وضعیت ربات و کاربر**

**🤖 وضعیت ربات:**
• ربات: {bot_status}
• مدت اجرا: {uptime_str}
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

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        reply_markup = get_public_section_markup()
        
        await update.message.reply_text(
            message,
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
• 📰 آخرین اخبار هوش مصنوعی از منابع معتبر
• 🌐 پیشرفت‌های جدید در دنیای AI

از دکمه زیر برای دسترسی به اخبار استفاده کنید:
        """
        
        # استفاده از کیبورد AI
        reply_markup = get_ai_menu_markup()
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    elif message_text == "📈 اخبار کریپتو":
        bot_logger.log_user_action(user.id, "CRYPTO_NEWS_REQUEST", "درخواست اخبار کریپتو")
        
        # نمایش پیام "در حال بارگذاری"
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار کریپتو از CoinDesk...")
        
        try:
            # دریافت اخبار کریپتو
            news_list = await fetch_coindesk_news()
            news_text = format_crypto_news_message(news_list)
            
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
                f"❌ خطا در دریافت اخبار کریپتو:\n{str(e)}",
                parse_mode='Markdown'
            )
        
        return
    
    elif message_text == "📺 اخبار عمومی":
        bot_logger.log_user_action(user.id, "GENERAL_NEWS_REQUEST", "درخواست اخبار عمومی")
        
        # نمایش پیام "در حال بارگذاری"
        loading_message = await update.message.reply_text("🔄 در حال دریافت آخرین اخبار روز از تسنیم...")
        
        try:
            # دریافت اخبار عمومی
            news_list = await fetch_tasnim_news()
            news_text = format_general_news_message(news_list)
            
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
    
    elif message_text == "📰 اخبار هوش مصنوعی":
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

async def main() -> None:
    """تابع اصلی برای راه‌اندازی ربات"""
    logger.info("🚀 شروع ربات تلگرام پیشرفته...")
    logger.info(f"🔑 BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
    logger.info(f"👤 ADMIN_USER_ID: {ADMIN_USER_ID}")
    logger.info(f"🌍 ENVIRONMENT: {ENVIRONMENT}")
    
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