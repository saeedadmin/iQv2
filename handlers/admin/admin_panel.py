#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
پنل مدیریت پیشرفته برای ربات تلگرام
شامل تمام قابلیت‌های مدیریتی و سیستمی
"""

import psutil
import platform
import os
import asyncio
import datetime
from typing import Dict, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.database import DatabaseManager, DatabaseLogger
from core.logger_system import bot_logger
from handlers.ai.multi_provider_handler import MultiProviderHandler

class AdminPanel:
    def __init__(self, db_manager: DatabaseManager, admin_user_id: int):
        """مقداردهی پنل ادمین"""
        self.db = db_manager
        self.admin_id = admin_user_id
        self.logger = DatabaseLogger(db_manager)
        self.bot_start_time = datetime.datetime.now()
    
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """ساخت کیبورد منوی اصلی ادمین - بهینه شده"""
        keyboard = [
            [
                InlineKeyboardButton("🖥️ سیستم", callback_data="admin_system"),
                InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📊 آمار", callback_data="admin_stats"),
                InlineKeyboardButton("💎 گزارش توکن‌های AI", callback_data="admin_ai_usage")
            ],
            [
                InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_system_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی سیستم - بهینه شده"""
        bot_status = "🟢" if self.db.is_bot_enabled() else "🔴"
        toggle_text = "خاموش" if self.db.is_bot_enabled() else "روشن"
        toggle_action = "sys_bot_disable" if self.db.is_bot_enabled() else "sys_bot_enable"
        
        keyboard = [
            [
                InlineKeyboardButton("💾 منابع", callback_data="sys_resources"),
                InlineKeyboardButton("📈 وضعیت", callback_data="sys_bot_status")
            ],
            [
                InlineKeyboardButton(f"{bot_status} {toggle_text} کردن", callback_data=toggle_action),
                InlineKeyboardButton("📊 لاگ سیستم", callback_data="sys_system_logs")
            ],
            [
                InlineKeyboardButton("🏠 منوی اصلی", callback_data="admin_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_users_menu_keyboard(self) -> InlineKeyboardMarkup:
        """کیبورد منوی مدیریت کاربران - بهینه شده"""
        stats = self.db.get_user_stats()
        keyboard = [
            [
                InlineKeyboardButton(f"📊 آمار ({stats['total']})", callback_data="users_stats"),
                InlineKeyboardButton("👥 لیست", callback_data="users_list")
            ],
            [
                InlineKeyboardButton(f"🚫 بلاک شده ({stats['blocked']})", callback_data="users_blocked"),
                InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("🏠 منوی اصلی", callback_data="admin_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def create_back_keyboard(self, back_to: str, refresh_action: str = None) -> InlineKeyboardMarkup:
        """ایجاد کیبورد بازگشت با امکان بروزرسانی"""
        buttons = []
        
        if refresh_action:
            buttons.append([
                InlineKeyboardButton("🔄 بروزرسانی", callback_data=refresh_action),
                InlineKeyboardButton("🏠 منوی اصلی", callback_data=back_to)
            ])
        else:
            buttons.append([
                InlineKeyboardButton("🏠 منوی اصلی", callback_data=back_to)
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    def get_system_resources(self) -> Dict:
        """دریافت اطلاعات منابع سیستم"""
        try:
            # CPU
            try:
                cpu_percent = psutil.cpu_percent(interval=0.5)  # کاهش زمان انتظار
                cpu_count = psutil.cpu_count()
            except Exception:
                cpu_percent = 0
                cpu_count = 'N/A'
            
            # Memory
            try:
                memory = psutil.virtual_memory()
                memory_total = round(memory.total / (1024**3), 2)  # GB
                memory_used = round(memory.used / (1024**3), 2)
                memory_percent = round(memory.percent, 1)
            except Exception:
                memory_total = 0
                memory_used = 0
                memory_percent = 0
            
            # Disk
            try:
                disk = psutil.disk_usage('/')
                disk_total = round(disk.total / (1024**3), 2)  # GB
                disk_used = round(disk.used / (1024**3), 2)
                disk_percent = round((disk.used / disk.total) * 100, 1)
            except Exception:
                disk_total = 0
                disk_used = 0
                disk_percent = 0
            
            # Network
            try:
                network = psutil.net_io_counters()
                bytes_sent = round(network.bytes_sent / (1024**2), 2)  # MB
                bytes_recv = round(network.bytes_recv / (1024**2), 2)
            except Exception:
                bytes_sent = 0
                bytes_recv = 0
            
            # Bot uptime
            try:
                uptime = datetime.datetime.now() - self.bot_start_time
                uptime_str = str(uptime).split('.')[0]  # حذف میکروثانیه
            except Exception:
                uptime_str = 'نامشخص'
            
            # Platform info
            try:
                platform_name = platform.system()
                platform_ver = platform.release()
                python_ver = platform.python_version()
            except Exception:
                platform_name = 'نامشخص'
                platform_ver = ''
                python_ver = 'نامشخص'
            
            return {
                'platform': platform_name,
                'platform_version': platform_ver,
                'python_version': python_ver,
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_total': memory_total,
                'memory_used': memory_used,
                'memory_percent': memory_percent,
                'disk_total': disk_total,
                'disk_used': disk_used,
                'disk_percent': disk_percent,
                'network_sent': bytes_sent,
                'network_recv': bytes_recv,
                'uptime': uptime_str
            }
        except Exception as e:
            return {'error': str(e)}
    
    def format_system_resources_message(self) -> str:
        """فرمت پیام منابع سیستم"""
        try:
            resources = self.get_system_resources()
            
            if 'error' in resources:
                return f"❌ خطا در دریافت اطلاعات سیستم:\n{resources['error']}"
            
            # Safe string formatting with proper escaping
            def safe_str(value, default='N/A'):
                if value is None or value == '':
                    return default
                # Escape any problematic characters for Markdown
                return str(value).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            
            # محاسبه فضای آزاد با مدیریت خطا
            try:
                memory_total = float(resources.get('memory_total', 0))
                memory_used = float(resources.get('memory_used', 0))
                memory_free = memory_total - memory_used
                
                disk_total = float(resources.get('disk_total', 0))
                disk_used = float(resources.get('disk_used', 0))
                disk_free = disk_total - disk_used
            except (ValueError, TypeError):
                memory_free = 0
                disk_free = 0
            
            message = "🖥️ *اطلاعات سیستم*\n\n"
            message += "*💻 پلتفرم:*\n"
            message += f"• سیستم‌عامل: {safe_str(resources.get('platform', 'نامشخص'))} {safe_str(resources.get('platform_version', ''))}\n"
            message += f"• پایتون: {safe_str(resources.get('python_version', 'نامشخص'))}\n"
            message += f"• مدت اجرا: {safe_str(resources.get('uptime', 'نامشخص'))}\n\n"
            
            message += "*⚡ CPU:*\n"
            message += f"• هسته‌ها: {safe_str(resources.get('cpu_count', 'N/A'))}\n"
            message += f"• مصرف: {safe_str(resources.get('cpu_percent', 'N/A'))}%\n\n"
            
            message += "*💾 حافظه:*\n"
            message += f"• کل: {safe_str(resources.get('memory_total', 'N/A'))} GB\n"
            message += f"• استفاده: {safe_str(resources.get('memory_used', 'N/A'))} GB"
            message += f" ({safe_str(resources.get('memory_percent', 'N/A'))}%)\n"
            message += f"• آزاد: {memory_free:.2f} GB\n\n"
            
            message += "*💿 دیسک:*\n"
            message += f"• کل: {safe_str(resources.get('disk_total', 'N/A'))} GB\n"
            message += f"• استفاده: {safe_str(resources.get('disk_used', 'N/A'))} GB"
            message += f" ({safe_str(resources.get('disk_percent', 'N/A'))}%)\n"
            message += f"• آزاد: {disk_free:.2f} GB\n\n"
            
            message += "*🌐 شبکه:*\n"
            message += f"• ارسال: {safe_str(resources.get('network_sent', 'N/A'))} MB\n"
            message += f"• دریافت: {safe_str(resources.get('network_recv', 'N/A'))} MB"
            
            return message
            
        except Exception as e:
            return f"❌ خطا در فرمت کردن اطلاعات سیستم: {str(e)}"
    
    def format_bot_status_message(self) -> str:
        """فرمت پیام وضعیت ربات"""
        stats = self.db.get_user_stats()
        bot_enabled = self.db.is_bot_enabled()
        
        status_emoji = "🟢" if bot_enabled else "🔴"
        status_text = "فعال" if bot_enabled else "غیرفعال"
        
        message = f"""
🤖 **وضعیت ربات**

**📊 وضعیت کلی:**
• ربات: {status_emoji} {status_text}
• زمان شروع: {self.bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}
• مدت اجرا: {datetime.datetime.now() - self.bot_start_time}

**👥 آمار کاربران:**
• کل کاربران: {stats['total']}
• کاربران فعال: {stats['active']}
• کاربران بلاک: {stats['blocked']}
• عضویت امروز: {stats['today']}

**📈 آمار عملکرد:**
• کل پیام‌ها: {stats['total_messages']}
• میانگین پیام روزانه: {stats['total_messages'] // max(1, (datetime.datetime.now() - self.bot_start_time).days or 1)}

**💾 دیتابیس:**
• وضعیت: ✅ متصل
• آخرین بک‌آپ: نیاز به پیاده‌سازی
        """
        return message
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت callback های پنل ادمین"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # بررسی دسترسی ادمین
        if user_id != self.admin_id:
            await query.edit_message_text("❌ شما دسترسی به این بخش ندارید.")
            return
        
        data = query.data
        
        # لاگ عملیات ادمین
        bot_logger.log_admin_action(user_id, data)
        
        try:
            if data == "admin_main":
                await self.show_main_menu(query)
            
            elif data == "admin_system":
                await self.show_system_menu(query)
            
            elif data == "admin_users":
                await self.show_users_menu(query)
            
            elif data == "admin_stats":
                await self.show_general_stats(query)
            
            elif data == "admin_logs":
                await self.show_logs_menu(query)
            
            elif data == "admin_ai_usage":
                await self.show_ai_usage_report(query)
            
            elif data == "sys_resources":
                await self.show_system_resources(query)
            
            elif data == "sys_bot_status":
                await self.show_bot_status(query)
            
            elif data == "sys_bot_disable":
                await self.disable_bot(query)
            
            elif data == "sys_bot_enable":
                await self.enable_bot(query)
            
            elif data == "sys_restart":
                await self.restart_bot(query)
            
            elif data == "sys_system_logs":
                await self.show_system_logs(query)
            
            elif data == "users_stats":
                await self.show_users_stats(query)
            
            elif data == "users_list":
                await self.show_users_list(query)
            
            elif data == "users_blocked":
                await self.show_blocked_users(query)
            
            elif data == "admin_refresh":
                await self.refresh_main_menu(query)
            
            elif data == "admin_close":
                await query.delete_message()
            
            # صفحه‌بندی لیست کاربران
            elif data.startswith("users_list_page_"):
                page = int(data.split("_")[-1])
                await self.show_users_list(query, page)
            
            # بن کردن کاربر
            elif data.startswith("user_block_"):
                user_id = int(data.split("_")[-1])
                await self.block_user(query, user_id)
            
            # آنبن کردن کاربر
            elif data.startswith("user_unblock_"):
                user_id = int(data.split("_")[-1])
                await self.unblock_user(query, user_id)
            
            else:
                await query.edit_message_text("❌ دستور نامعتبر")
                
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در پردازش: {str(e)}")
    
    async def show_main_menu(self, query):
        """نمایش منوی اصلی"""
        import html
        safe_first_name = html.escape(query.from_user.first_name or "ادمین")
        
        message = f"""
🔧 <b>پنل مدیریت ربات</b>

👨‍💼 ادمین: {safe_first_name}
🕐 زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

یک گزینه را انتخاب کنید:
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_menu_keyboard(),
            parse_mode='HTML'
        )
    
    async def show_system_menu(self, query):
        """نمایش منوی سیستم"""
        message = """
🖥️ **مدیریت سیستم**

در این بخش می‌توانید:
• وضعیت منابع سیستم را مشاهده کنید
• ربات را خاموش/روشن کنید  
• لاگ‌های سیستم را بررسی کنید
• ربات را ری‌استارت کنید

یک گزینه را انتخاب کنید:
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_system_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_users_menu(self, query):
        """نمایش منوی کاربران"""
        stats = self.db.get_user_stats()
        message = f"""
👥 **مدیریت کاربران**

**📊 آمار سریع:**
• کل کاربران: {stats['total']}
• فعال: {stats['active']} | بلاک: {stats['blocked']}
• عضویت امروز: {stats['today']}

یک گزینه را انتخاب کنید:
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_users_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_general_stats(self, query):
        """نمایش آمار کلی"""
        stats = self.db.get_user_stats()
        resources = self.get_system_resources()
        
        message = f"""
📊 **آمار کلی ربات**

**👥 کاربران:**
• کل: {stats['total']}
• فعال: {stats['active']}
• بلاک شده: {stats['blocked']}
• عضویت امروز: {stats['today']}

**📈 فعالیت:**
• کل پیام‌ها: {stats['total_messages']}
• مدت اجرا: {datetime.datetime.now() - self.bot_start_time}

**💻 سیستم:**
• CPU: {resources.get('cpu_percent', 'N/A')}%
• RAM: {resources.get('memory_percent', 'N/A')}%
• دیسک: {resources.get('disk_percent', 'N/A')}%

**🤖 وضعیت ربات:**
• {"🟢 فعال" if self.db.is_bot_enabled() else "🔴 غیرفعال"}
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_back_keyboard("admin_main", "admin_stats"),
            parse_mode='Markdown'
        )
    
    async def show_recent_logs(self, query):
        """نمایش خلاصه ۱۰ لاگ اخیر - نسخه ساده"""
        try:
            logs = self.db.get_recent_logs(10)  # فقط 10 مورد
            
            if not logs:
                message = "📋 **خلاصه لاگ‌های اخیر**\n\nهیچ لاگی یافت نشد."
            else:
                message = "📋 **خلاصه ۱۰ لاگ اخیر:**\n\n"
                for i, log in enumerate(logs, 1):
                    try:
                        # پردازش timestamp با مدیریت خطا
                        timestamp_str = str(log['timestamp'])
                        if len(timestamp_str) > 19:
                            # فقط ساعت و دقیقه را نمایش دهیم
                            time_part = timestamp_str[11:16]
                        else:
                            time_part = timestamp_str[-8:-3] if len(timestamp_str) >= 8 else timestamp_str
                        
                        level = str(log.get('level', 'INFO'))
                        message_text = str(log.get('message', 'پیام خالی'))
                        
                        level_emoji = {
                            "INFO": "ℹ️", 
                            "WARNING": "⚠️", 
                            "ERROR": "❌", 
                            "USER_ACTION": "👤", 
                            "ADMIN_ACTION": "👨‍💼", 
                            "SYSTEM": "🖥️"
                        }.get(level, "📝")
                        
                        # محدود کردن طول پیام برای نمایش بهتر
                        if len(message_text) > 40:
                            display_message = message_text[:37] + "..."
                        else:
                            display_message = message_text
                        
                        message += f"{i}. {level_emoji} `{time_part}` {display_message}\n"
                        
                    except Exception as e:
                        message += f"{i}. 📝 `خطا` {str(e)[:25]}...\n"
                        
        except Exception as e:
            message = f"❌ خطا در دریافت لاگ‌ها: {str(e)}"
        
        # دکمه ساده برای بازگشت
        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_logs"),
                InlineKeyboardButton("🏠 منوی اصلی", callback_data="admin_main")
            ]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def show_system_resources(self, query):
        """نمایش منابع سیستم"""
        message = self.format_system_resources_message()
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="sys_resources")],
            [InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def show_bot_status(self, query):
        """نمایش وضعیت ربات"""
        message = self.format_bot_status_message()
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="sys_bot_status")],
            [InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def disable_bot(self, query):
        """غیرفعال کردن ربات"""
        success = self.db.set_bot_enabled(False)
        if success:
            bot_logger.log_admin_action(query.from_user.id, "BOT_DISABLED")
            message = "🔴 **ربات غیرفعال شد**\n\nربات برای کاربران عادی دسترسی ندارد.\nادمین همچنان دسترسی کامل دارد."
        else:
            message = "❌ خطا در غیرفعال کردن ربات"
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def enable_bot(self, query):
        """فعال کردن ربات"""
        success = self.db.set_bot_enabled(True)
        if success:
            bot_logger.log_admin_action(query.from_user.id, "BOT_ENABLED")
            message = "🟢 **ربات فعال شد**\n\nربات برای تمام کاربران قابل دسترسی است."
        else:
            message = "❌ خطا در فعال کردن ربات"
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def restart_bot(self, query):
        """ری‌استارت ربات"""
        bot_logger.log_admin_action(query.from_user.id, "BOT_RESTART_REQUESTED")
        
        message = """
🔄 **درخواست ری‌استارت ربات**

⚠️ **توجه:** ری‌استارت ربات نیاز به دسترسی سرور دارد.

در حالت عادی:
• ربات باید از طریق PM2 یا سرویس سیستم مدیریت شود
• دستور ری‌استارت از طریق terminal: `sudo systemctl restart telegram-bot`
• یا از طریق PM2: `pm2 restart telegram-bot`

**📋 وضعیت فعلی:**
• ربات: 🟢 در حال اجرا
• آخرین ری‌استارت: {self.bot_start_time.strftime('%Y/%m/%d %H:%M')}
• مدت اجرا: {datetime.datetime.now() - self.bot_start_time}

💡 برای ری‌استارت واقعی، از منوی سرور استفاده کنید.
        """
        
        restart_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بروزرسانی منو", callback_data="admin_main"),
                InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")
            ]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=restart_keyboard,
            parse_mode='Markdown'
        )
    
    async def show_system_logs(self, query):
        """نمایش لاگ‌های سیستم"""
        try:
            # دریافت لاگ‌های سیستم فقط
            all_logs = self.db.get_recent_logs(50)
            system_logs = [log for log in all_logs if log.get('level') in ['SYSTEM', 'ERROR', 'ADMIN_ACTION']]
            
            if not system_logs:
                message = "📊 **لاگ‌های سیستم**\n\nهیچ لاگ سیستمی یافت نشد."
            else:
                message = f"📊 **لاگ‌های سیستم** ({len(system_logs)} مورد):\n\n"
                for log in system_logs[:8]:  # فقط 8 مورد آخر
                    try:
                        timestamp_str = str(log['timestamp'])
                        if len(timestamp_str) > 16:
                            timestamp = timestamp_str[5:16]  # فقط ماه-روز ساعت
                        else:
                            timestamp = timestamp_str
                        
                        level = str(log.get('level', 'SYSTEM'))
                        message_text = str(log.get('message', ''))
                        
                        level_emoji = {
                            "SYSTEM": "🖥️", 
                            "ERROR": "❌", 
                            "ADMIN_ACTION": "👨‍💼"
                        }.get(level, "📝")
                        
                        # محدود کردن طول پیام
                        if len(message_text) > 40:
                            display_message = message_text[:37] + "..."
                        else:
                            display_message = message_text
                        
                        message += f"{level_emoji} `{timestamp}` {display_message}\n"
                        
                    except Exception as e:
                        message += f"📝 خطا در پردازش لاگ: {str(e)[:20]}...\n"
                        
        except Exception as e:
            message = f"❌ خطا در دریافت لاگ‌های سیستم: {str(e)}"
        
        back_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 بروزرسانی", callback_data="sys_system_logs"),
                InlineKeyboardButton("📋 همه لاگ‌ها", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton("🖥️ منوی سیستم", callback_data="admin_system")
            ]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def show_users_stats(self, query):
        """نمایش آمار تفصیلی کاربران"""
        stats = self.db.get_user_stats()
        all_users = self.db.get_all_users()
        
        # محاسبه آمار اضافی
        recent_users = len([u for u in all_users if 
                           datetime.datetime.fromisoformat(u['join_date'].replace('Z', '+00:00')).date() >= 
                           (datetime.date.today() - datetime.timedelta(days=7))])
        
        active_today = len([u for u in all_users if 
                           datetime.datetime.fromisoformat(u['last_activity'].replace('Z', '+00:00')).date() == 
                           datetime.date.today()])
        
        message = f"""
📊 **آمار تفصیلی کاربران**

**📈 آمار کلی:**
• کل کاربران: {stats['total']}
• کاربران فعال: {stats['active']}
• کاربران بلاک: {stats['blocked']}

**📅 آمار زمانی:**
• عضویت امروز: {stats['today']}
• عضویت 7 روز اخیر: {recent_users}
• فعال امروز: {active_today}

**💬 آمار پیام:**
• کل پیام‌ها: {stats['total_messages']}
• میانگین پیام هر کاربر: {stats['total_messages'] // max(1, stats['total']) if stats['total'] > 0 else 0}

**📊 نرخ فعالیت:**
• نرخ کاربران فعال: {(stats['active'] / max(1, stats['total']) * 100):.1f}%
• نرخ کاربران بلاک: {(stats['blocked'] / max(1, stats['total']) * 100):.1f}%
        """
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def show_users_list(self, query, page: int = 0):
        """نمایش لیست کاربران با صفحه‌بندی"""
        try:
            users = self.db.get_all_users()
            users_per_page = 5
            start_index = page * users_per_page
            end_index = start_index + users_per_page
            
            # تابع escape برای Markdown
            def safe_text(text, default='نامشخص'):
                if not text:
                    return default
                # Escape کردن کاراکترهای خاص Markdown
                return str(text).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
            
            if not users:
                message = "👥 *لیست کاربران*\n\nهیچ کاربری یافت نشد."
                keyboard = [[InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]]
            else:
                current_users = users[start_index:end_index]
                total_pages = (len(users) + users_per_page - 1) // users_per_page
                
                message = f"👥 *لیست کاربران* (صفحه {page + 1} از {total_pages})\n"
                message += f"کل کاربران: {len(users)}\n\n"
                
                for i, user in enumerate(current_users, start=start_index + 1):
                    status = "🚫 بلاک" if user['is_blocked'] else "✅ فعال"
                    
                    # Safe formatting برای نام کاربری
                    if user['username']:
                        username = f"@{safe_text(user['username'])}"
                    else:
                        username = "بدون نام کاربری"
                    
                    join_date = user['join_date'][:10] if user['join_date'] else "نامشخص"
                    first_name = safe_text(user['first_name'], 'نام نامشخص')
                    
                    message += f"*{i}.* {first_name}\n"
                    message += f"   • نام کاربری: {username}\n"
                    message += f"   • ID: `{user['user_id']}`\n"
                    message += f"   • وضعیت: {status}\n"
                    message += f"   • تاریخ عضویت: {join_date}\n"
                    message += f"   • تعداد پیام: {user['message_count']}\n\n"
                
                # دکمه‌های مدیریت
                keyboard = []
                
                # دکمه‌های کاربران برای بن/آنبن
                user_buttons = []
                for user in current_users:
                    # Safe text برای نام در دکمه‌ها
                    safe_name = safe_text(user['first_name'], 'کاربر')[:8]
                    if user['is_blocked']:
                        user_buttons.append(InlineKeyboardButton(
                            f"🔓 آنبن {safe_name}", 
                            callback_data=f"user_unblock_{user['user_id']}"
                        ))
                    else:
                        user_buttons.append(InlineKeyboardButton(
                            f"🚫 بن {safe_name}", 
                            callback_data=f"user_block_{user['user_id']}"
                        ))
                
                # تقسیم دکمه‌ها به ردیف‌هایی با حداکثر 2 دکمه
                for i in range(0, len(user_buttons), 2):
                    keyboard.append(user_buttons[i:i+2])
                
                # دکمه‌های صفحه‌بندی
                nav_buttons = []
                if page > 0:
                    nav_buttons.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"users_list_page_{page-1}"))
                if page < total_pages - 1:
                    nav_buttons.append(InlineKeyboardButton("▶️ بعدی", callback_data=f"users_list_page_{page+1}"))
                
                if nav_buttons:
                    keyboard.append(nav_buttons)
                
                # دکمه بازگشت
                keyboard.append([InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            # Fallback به HTML parsing اگر Markdown کار نکرد
            await query.edit_message_text(
                f"❌ خطا در نمایش لیست: {str(e)}\n\nبرای رفع مشکل، از منوی اصلی استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
                ])
            )
    
    async def show_blocked_users(self, query):
        """نمایش کاربران بلاک شده"""
        all_users = self.db.get_all_users()
        blocked_users = [u for u in all_users if u['is_blocked']]
        
        if not blocked_users:
            message = "🚫 **کاربران بلاک شده**\n\nهیچ کاربر بلاک شده‌ای یافت نشد."
        else:
            message = f"🚫 **کاربران بلاک شده** ({len(blocked_users)} کاربر):\n\n"
            for i, user in enumerate(blocked_users[:10]):
                # Escape کردن نام و یوزرنیم
                safe_first_name = str(user['first_name'] or 'کاربر').replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                if user['username']:
                    safe_username = str(user['username']).replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                    username = f"@{safe_username}"
                else:
                    username = "بدون نام کاربری"
                message += f"{i+1}. {safe_first_name} ({username})\n"
                message += f"   └ ID: `{user['user_id']}`\n"
            
            if len(blocked_users) > 10:
                message += f"\n... و {len(blocked_users) - 10} کاربر دیگر"
        
        back_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=back_keyboard,
            parse_mode='Markdown'
        )
    
    async def block_user(self, query, user_id: int):
        """بن کردن کاربر"""
        try:
            user_info = self.db.get_user(user_id)
            if not user_info:
                message = "❌ کاربر یافت نشد!"
            elif user_info['is_blocked']:
                # Escape کردن نام کاربر
                safe_name = str(user_info['first_name'] or 'کاربر').replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                message = f"⚠️ کاربر {safe_name} قبلاً بلاک شده است."
            else:
                success = self.db.block_user(user_id)
                if success:
                    # Escape کردن نام کاربر
                    safe_name = str(user_info['first_name'] or 'کاربر').replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                    bot_logger.log_admin_action(query.from_user.id, f"USER_BLOCKED", f"User {user_id} blocked")
                    message = f"🚫 کاربر {safe_name} با موفقیت بلاک شد."
                else:
                    message = "❌ خطا در بلاک کردن کاربر"
            
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 بازگشت به لیست", callback_data="users_list")],
                [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ خطا در پردازش: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
                ])
            )
    
    async def unblock_user(self, query, user_id: int):
        """آنبن کردن کاربر"""
        try:
            user_info = self.db.get_user(user_id)
            if not user_info:
                message = "❌ کاربر یافت نشد!"
            elif not user_info['is_blocked']:
                # Escape کردن نام کاربر
                safe_name = str(user_info['first_name'] or 'کاربر').replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                message = f"⚠️ کاربر {safe_name} قبلاً آزاد است."
            else:
                success = self.db.unblock_user(user_id)
                if success:
                    # Escape کردن نام کاربر
                    safe_name = str(user_info['first_name'] or 'کاربر').replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[').replace(']', '\\]')
                    bot_logger.log_admin_action(query.from_user.id, f"USER_UNBLOCKED", f"User {user_id} unblocked")
                    message = f"🔓 کاربر {safe_name} با موفقیت آزاد شد."
                else:
                    message = "❌ خطا در آزاد کردن کاربر"
            
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 بازگشت به لیست", callback_data="users_list")],
                [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ خطا در پردازش: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 منوی کاربران", callback_data="admin_users")]
                ])
            )
    
    async def show_logs_menu(self, query):
        """نمایش لاگ‌های اخیر - نسخه ساده شده"""
        await self.show_recent_logs(query)
    
    async def show_ai_usage_report(self, query):
        """نمایش گزارش استفاده از توکن‌های AI"""
        try:
            message = "🔄 **در حال بررسی وضعیت AI Providers...**\n\nلطفاً کمی صبر کنید."
            await query.edit_message_text(message, parse_mode='Markdown')
            
            # ایجاد MultiProviderHandler
            ai_handler = MultiProviderHandler(self.db)
            
            # جمع‌آوری اطلاعات usage از هر provider
            usage_report = await self._get_ai_usage_report(ai_handler)
            
            # فرمت کردن گزارش
            formatted_report = self._format_ai_usage_message(usage_report)
            
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_ai_usage")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="admin_main")]
            ])
            
            await query.edit_message_text(
                formatted_report,
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            error_message = f"❌ **خطا در دریافت گزارش AI:**\n\n`{str(e)}`"
            
            back_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="admin_ai_usage")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="admin_main")]
            ])
            
            await query.edit_message_text(
                error_message,
                reply_markup=back_keyboard,
                parse_mode='Markdown'
            )
    
    async def _get_ai_usage_report(self, ai_handler: MultiProviderHandler) -> Dict:
        """جمع‌آوری اطلاعات usage از تمام AI providers"""
        import requests
        import asyncio
        
        usage_data = {}
        
        # تعریف providers که قابلیت check usage دارند
        usage_checkers = {
            "groq": self._check_groq_usage,
            "cerebras": self._check_cerebras_usage, 
            "gemini": self._check_gemini_usage,
            "cohere": self._check_cohere_usage
            # OpenRouter غیرفعال شده
        }
        
        # بررسی هر provider
        for provider_name in ai_handler.providers.keys():
            try:
                if provider_name in usage_checkers and provider_name in ai_handler.key_rotators:
                    usage_info = await usage_checkers[provider_name](ai_handler, provider_name)
                    usage_data[provider_name] = usage_info
                else:
                    usage_data[provider_name] = {
                        "status": "not_supported",
                        "message": "این provider قابلیت بررسی usage ندارد"
                    }
            except Exception as e:
                usage_data[provider_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return usage_data
    
    async def _check_groq_usage(self, ai_handler: MultiProviderHandler, provider_name: str) -> Dict:
        """بررسی usage Groq"""
        try:
            import requests
            
            if provider_name not in ai_handler.key_rotators:
                return {"status": "no_keys", "message": "API Key یافت نشد"}
            
            # گرفتن یکی از کلیدهای Groq
            key_rotator = ai_handler.key_rotators[provider_name]
            api_key = key_rotator.get_next_key()
            
            if not api_key:
                return {"status": "no_keys", "message": "API Key فعال یافت نشد"}
            
            # Groq endpoint درست شده
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # امتحان کردن endpoint درست
            response = requests.get("https://api.groq.com/usage/limits", headers=headers, timeout=10)
            
            # اگر این endpoint کار نکرد، از endpoint دیگه استفاده کن
            if response.status_code != 200:
                response = requests.get("https://api.groq.com/openai/v1/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Groq معمولاً اطلاعات usage رو در response نمیده
                # فقط اطلاعات rate limit
                return {
                    "status": "partial",
                    "provider": "Groq", 
                    "message": "API فعال است (اطلاعات usage مستقیم در دسترس نیست)",
                    "note": "Groq rate limits: 1000 requests/min, 14400 requests/day",
                    "api_response": "OK",
                    "response_time": f"{datetime.datetime.now().strftime('%H:%M:%S')}"
                }
            else:
                return {
                    "status": "api_error", 
                    "error_code": response.status_code,
                    "message": f"خطای API: {response.status_code}",
                    "api_key_status": "ناکارآمد" if response.status_code in [401, 403] else "خطای نامشخص"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "خطا در دریافت اطلاعات Groq"
            }
    
    async def _check_cerebras_usage(self, ai_handler: MultiProviderHandler, provider_name: str) -> Dict:
        """بررسی usage Cerebras با rate limits"""
        try:
            # Cerebras اطلاعات usage رو در response headers میده
            # از internal tracking هم استفاده می‌کنیم
            if provider_name in ai_handler.provider_performance:
                perf_data = ai_handler.provider_performance[provider_name]
                return {
                    "status": "partial",
                    "provider": "Cerebras",
                    "message": "Rate limits در headers موجود",
                    "rate_limit_headers": "x-ratelimit-*",
                    "note": "Real-time rate limits از API headers",
                    "performance_stats": perf_data,
                    "suggested_check": "API response headers",
                    "response_time": f"{datetime.datetime.now().strftime('%H:%M:%S')}"
                }
            else:
                return {
                    "status": "no_data",
                    "provider": "Cerebras",
                    "message": "هنوز usage یافت نشده",
                    "suggested_check": "استفاده از AI برای شروع tracking"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "خطا در بررسی Cerebras"
            }
    
    async def _check_gemini_usage(self, ai_handler: MultiProviderHandler, provider_name: str) -> Dict:
        """بررسی usage Gemini - بدون API endpoint مستقیم"""
        try:
            # Gemini هیچ endpoint برای programmatic usage check نداره
            # پیشنهاد استفاده از internal tracking و Google Cloud Console
            return {
                "status": "no_api_endpoint",
                "provider": "Gemini",
                "message": "API endpoint برای usage monitoring موجود نیست",
                "alternatives": [
                    "Google AI Studio Console (https://aistudio.google.com/usage)",
                    "Google Cloud Console Quotas",
                    "Internal tracking system (database)"
                ],
                "rate_limits": "50 requests/day, 1,000 requests/minute",
                "manual_check_url": "https://aistudio.google.com/usage",
                "note": "مصرف در internal database ذخیره می‌شود",
                "response_time": f"{datetime.datetime.now().strftime('%H:%M:%S')}"
            }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "خطا در بررسی Gemini"
            }
    

    
    async def _check_cohere_usage(self, ai_handler: MultiProviderHandler, provider_name: str) -> Dict:
        """بررسی usage Cohere"""
        try:
            # Cohere اطلاعات usage رو در response نمیده
            # فقط می‌تونیم از performance tracking استفاده کنیم
            if provider_name in ai_handler.provider_performance:
                perf_data = ai_handler.provider_performance[provider_name]
                return {
                    "status": "partial",
                    "provider": "Cohere", 
                    "total_requests": perf_data.get("total_requests", 0),
                    "successful_requests": perf_data.get("successful_requests", 0),
                    "success_rate": f"{perf_data.get('success_rate', 0):.1f}%",
                    "avg_response_time": f"{perf_data.get('avg_response_time', 0):.2f}s",
                    "message": "اطلاعات عملکرد از ربات (usage مستقیم در دسترس نیست)"
                }
            else:
                return {
                    "status": "no_data",
                    "provider": "Cohere",
                    "message": "هنوز درخواستی انجام نشده"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e), 
                "message": "خطا در دریافت اطلاعات Cohere"
            }
    
    def _format_ai_usage_message(self, usage_data: Dict) -> str:
        """فرمت کردن پیام گزارش AI usage"""
        message = "💎 **گزارش استفاده از توکن‌های AI**\n\n"
        message += f"🕐 تاریخ: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if not usage_data:
            message += "❌ هیچ provider یافت نشد."
            return message
        
        for provider_name, data in usage_data.items():
            provider_display = data.get("provider", provider_name.title())
            status = data.get("status", "unknown")
            
            # انتخاب ایموجی بر اساس وضعیت
            status_emoji = {
                "success": "🟢",
                "partial": "🟡", 
                "limited": "🟠",
                "no_data": "⚪",
                "no_keys": "🔴",
                "api_error": "🔴",
                "error": "❌",
                "not_supported": "⚪",
                "no_api_endpoint": "🔵"  # Gemini
            }.get(status, "❓")
            
            message += f"**{status_emoji} {provider_display}:**\n"
            
            # نمایش اطلاعات بر اساس نوع
            if status == "success":
                if "total_requests" in data:
                    message += f"  • کل درخواست‌ها: {data['total_requests']}\n"
                    message += f"  • کل توکن‌ها: {data['total_tokens']:,}\n"
                    message += f"  • توکن باقی‌مانده: {data['remaining_tokens']}\n"
                    message += f"  • درخواست‌های امروز: {data['requests_today']}\n"
                elif "credits_total" in data:
                    message += f"  • کل اعتبار: {data['credits_total']:,.2f}\n"
                    message += f"  • اعتبار استفاده شده: {data['credits_used']:,.2f}\n"
                    message += f"  • اعتبار باقی‌مانده: {data['credits_remaining']:,.2f}\n"
                    
            elif status == "partial":
                message += f"  • کل درخواست‌ها: {data.get('total_requests', 0)}\n"
                message += f"  • درخواست‌های موفق: {data.get('successful_requests', 0)}\n"
                message += f"  • نرخ موفقیت: {data.get('success_rate', '0%')}\n"
                message += f"  • میانگین زمان پاسخ: {data.get('avg_response_time', '0s')}\n"
                
            elif status == "limited":
                message += f"  • {data.get('message', 'محدودیت API')}\n"
                if "note" in data:
                    message += f"  • نکته: {data['note']}\n"
                    
            elif status == "no_api_endpoint":
                # مخصوص Gemini
                message += f"  • {data.get('message', 'API endpoint در دسترس نیست')}\n"
                if "alternatives" in data:
                    message += "  • روش‌های بررسی:\n"
                    for alt in data["alternatives"]:
                        message += f"    - {alt}\n"
                if "rate_limits" in data:
                    message += f"  • محدودیت‌ها: {data['rate_limits']}\n"
                if "manual_check_url" in data:
                    message += f"  • لینک بررسی دستی: {data['manual_check_url']}\n"
                if "note" in data:
                    message += f"  • نکته: {data['note']}\n"
                    
            elif status == "no_data":
                message += f"  • {data.get('message', 'اطلاعاتی موجود نیست')}\n"
                
            elif status in ["no_keys", "error", "api_error"]:
                message += f"  • {data.get('message', 'خطا در دریافت اطلاعات')}\n"
                if "error" in data:
                    message += f"  • جزئیات خطا: `{data['error'][:50]}{'...' if len(data['error']) > 50 else ''}`\n"
                if "error_code" in data:
                    message += f"  • کد خطا: `{data['error_code']}`\n"
                    
            else:
                message += f"  • {data.get('message', 'وضعیت نامشخص')}\n"
            
            message += "\n"
        
        # خلاصه کلی
        total_providers = len(usage_data)
        successful_providers = len([d for d in usage_data.values() if d.get("status") == "success"])
        active_providers = len([d for d in usage_data.values() if d.get("status") in ["success", "partial"]])
        
        message += f"**📊 خلاصه کلی:**\n"
        message += f"• کل providers: {total_providers}\n"
        message += f"• providers فعال: {active_providers}\n"
        message += f"• providers با اطلاعات کامل: {successful_providers}\n\n"
        
        # آمار دقیق از database tracking (برای تمام providers)
        try:
            db_stats = ai_handler.get_usage_stats(days=30)
            if db_stats:
                message += "**📈 آمار تفصیلی از Database (۳۰ روز گذشته):**\n"
                
                for provider_name, stats in db_stats.items():
                    message += f"**{provider_name.title()}:**\n"
                    message += f"  • کل درخواست‌ها: {stats['total_requests']:,}\n"
                    message += f"  • کل توکن‌های استفاده شده: {stats['total_tokens']:,}\n"
                    message += f"  • توکن‌های prompt: {stats['total_prompt_tokens']:,}\n"
                    message += f"  • توکن‌های completion: {stats['total_completion_tokens']:,}\n"
                    message += f"  • میانگین توکن هر درخواست: {stats.get('avg_tokens_per_request', 0):.0f}\n"
                    if stats.get('total_cost', 0) > 0:
                        message += f"  • تخمین هزینه: ${stats['total_cost']:.4f}\n"
                    if stats.get('last_date'):
                        message += f"  • آخرین استفاده: {stats['last_date']}\n"
                    message += "\n"
                    
        except Exception as e:
            message += f"**⚠️ خطا در دریافت آمار database:** `{str(e)[:50]}...`\n"
        
        return message
    

    
    async def refresh_main_menu(self, query):
        """بروزرسانی منوی اصلی"""
        await self.show_main_menu(query)
        await query.answer("🔄 بروزرسانی شد!")
