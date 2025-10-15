#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web Server برای اجرای ربات تلگرام در WEB service
این فایل یک HTTP server ساده ایجاد می‌کند و ربات تلگرام را در پس‌زمینه اجرا می‌کند
"""

import os
import asyncio
import threading
import datetime
import logging
from aiohttp import web
import subprocess
import sys

# تنظیمات logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# متغیرهای محیطی
PORT = int(os.getenv('PORT', 8000))
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')

# متغیر global برای وضعیت ربات
bot_process = None
bot_status = "starting"

async def health_check(request):
    """Health check endpoint"""
    global bot_status
    return web.json_response({
        "status": "healthy",
        "bot_status": bot_status,
        "timestamp": datetime.datetime.now().isoformat(),
        "service": "telegram-bot-web",
        "port": PORT,
        "bot_token_configured": bool(BOT_TOKEN),
        "admin_configured": bool(ADMIN_USER_ID)
    })

async def bot_status_endpoint(request):
    """وضعیت ربات"""
    global bot_process, bot_status
    
    status_info = {
        "bot_status": bot_status,
        "process_running": bot_process and bot_process.poll() is None,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    if bot_process:
        status_info["process_id"] = bot_process.pid
        status_info["return_code"] = bot_process.poll()
    
    return web.json_response(status_info)

def run_telegram_bot():
    """اجرای ربات تلگرام مستقیماً (بدون subprocess)"""
    global bot_status
    
    try:
        logger.info("🤖 شروع ربات تلگرام...")
        bot_status = "starting"
        
        # import و اجرای ربات تلگرام
        from telegram_bot import main as telegram_main
        
        bot_status = "running"
        logger.info("✅ ربات تلگرام شروع شد")
        
        # اجرای ربات
        telegram_main()
        
        bot_status = "stopped"
        logger.info("ربات تلگرام متوقف شد")
            
    except Exception as e:
        bot_status = "error"
        logger.error(f"❌ خطا در اجرای ربات تلگرام: {e}")

async def start_background_bot():
    """شروع ربات در background"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_telegram_bot)

def create_app():
    """ایجاد web application"""
    app = web.Application()
    
    # تعریف route ها
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/bot-status', bot_status_endpoint)
    
    return app

async def init_app():
    """راه‌اندازی اولیه"""
    logger.info("🌐 راه‌اندازی Web Server...")
    
    # بررسی متغیرهای محیطی
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN تعریف نشده است!")
        return None
        
    if not ADMIN_USER_ID:
        logger.error("❌ ADMIN_USER_ID تعریف نشده است!")
        return None
    
    # ایجاد app
    app = create_app()
    
    # شروع ربات در background
    asyncio.create_task(start_background_bot())
    
    return app

def main():
    """تابع اصلی"""
    try:
        logger.info("🚀 شروع Web Server برای ربات تلگرام...")
        logger.info(f"📡 پورت: {PORT}")
        logger.info(f"🔑 Bot Token: {'✅' if BOT_TOKEN else '❌'}")
        logger.info(f"👨‍💼 Admin ID: {'✅' if ADMIN_USER_ID else '❌'}")
        
        # ایجاد و اجرای server
        web.run_app(
            init_app(),
            host='0.0.0.0',
            port=PORT,
            access_log=logger
        )
        
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی Web Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
