#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت پیشرفته کاربران
شامل عملیات مدیریتی و کمکی برای کاربران
"""

import asyncio
from typing import List, Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
from database.database import DatabaseManager, DatabaseLogger

class UserManager:
    def __init__(self, db_manager: DatabaseManager, bot_token: str):
        """مقداردهی مدیر کاربران"""
        self.db = db_manager
        self.logger = DatabaseLogger(db_manager)
        self.bot_token = bot_token
    
    async def send_message_to_user(self, bot: Bot, user_id: int, message: str, 
                                   parse_mode: str = 'Markdown') -> bool:
        """ارسال پیام به کاربر خاص"""
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            self.logger.log_system_event(
                "MESSAGE_FAILED", 
                f"خطا در ارسال پیام به {user_id}: {str(e)}"
            )
            
            # اگر کاربر ربات را بلاک کرده، او را بلاک کن
            if "blocked by the user" in str(e).lower():
                self.db.block_user(user_id)
                self.logger.log_admin_action(None, "AUTO_BLOCK", user_id)
            
            return False
    
    async def bulk_message_send(self, bot: Bot, user_ids: List[int], 
                               message: str, delay: float = 0.1) -> Dict[str, int]:
        """ارسال پیام انبوه با گزارش تفصیلی"""
        results = {
            'success': 0,
            'failed': 0,
            'blocked': 0,
            'not_found': 0,
            'rate_limited': 0
        }
        
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                results['success'] += 1
                
            except TelegramError as e:
                error_str = str(e).lower()
                
                if "blocked by the user" in error_str:
                    results['blocked'] += 1
                    self.db.block_user(user_id)
                elif "user not found" in error_str:
                    results['not_found'] += 1
                    self.db.block_user(user_id)  # کاربر حساب خود را حذف کرده
                elif "too many requests" in error_str:
                    results['rate_limited'] += 1
                    await asyncio.sleep(1)  # تأخیر بیشتر برای rate limit
                else:
                    results['failed'] += 1
                
                self.logger.log_system_event(
                    "BULK_MESSAGE_ERROR", 
                    f"خطا در ارسال به {user_id}: {str(e)}"
                )
            
            # تأخیر بین ارسال پیام‌ها
            await asyncio.sleep(delay)
        
        return results
    
    def get_user_statistics(self) -> Dict:
        """دریافت آمار تفصیلی کاربران"""
        all_users = self.db.get_all_users()
        
        if not all_users:
            return {}
        
        # آمار پایه
        total_users = len(all_users)
        active_users = len([u for u in all_users if not u['is_blocked']])
        blocked_users = len([u for u in all_users if u['is_blocked']])
        
        # آمار پیام‌ها
        total_messages = sum(u['message_count'] for u in all_users)
        avg_messages_per_user = total_messages / total_users if total_users > 0 else 0
        
        # کاربران پرفعالیت (بیش از میانگین پیام)
        active_threshold = avg_messages_per_user
        highly_active = len([u for u in all_users if u['message_count'] > active_threshold])
        
        # آمار زمانی
        import datetime
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        month_ago = today - datetime.timedelta(days=30)
        
        users_today = len([u for u in all_users if 
                          datetime.datetime.fromisoformat(u['join_date'].replace('Z', '+00:00')).date() == today])
        
        users_this_week = len([u for u in all_users if 
                              datetime.datetime.fromisoformat(u['join_date'].replace('Z', '+00:00')).date() >= week_ago])
        
        users_this_month = len([u for u in all_users if 
                               datetime.datetime.fromisoformat(u['join_date'].replace('Z', '+00:00')).date() >= month_ago])
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'total_messages': total_messages,
            'avg_messages_per_user': round(avg_messages_per_user, 2),
            'highly_active_users': highly_active,
            'users_today': users_today,
            'users_this_week': users_this_week,
            'users_this_month': users_this_month,
            'activity_rate': round((active_users / total_users * 100), 2) if total_users > 0 else 0,
            'block_rate': round((blocked_users / total_users * 100), 2) if total_users > 0 else 0
        }
    
    def find_users_by_criteria(self, criteria: Dict) -> List[Dict]:
        """جستجوی کاربران بر اساس معیارهای مختلف"""
        all_users = self.db.get_all_users()
        filtered_users = []
        
        for user in all_users:
            match = True
            
            # فیلتر بر اساس وضعیت بلاک
            if 'is_blocked' in criteria:
                if user['is_blocked'] != criteria['is_blocked']:
                    match = False
            
            # فیلتر بر اساس تعداد پیام‌ها
            if 'min_messages' in criteria:
                if user['message_count'] < criteria['min_messages']:
                    match = False
            
            if 'max_messages' in criteria:
                if user['message_count'] > criteria['max_messages']:
                    match = False
            
            # فیلتر بر اساس نام
            if 'name_contains' in criteria:
                name_search = criteria['name_contains'].lower()
                user_name = (user['first_name'] or '').lower()
                if name_search not in user_name:
                    match = False
            
            # فیلتر بر اساس نام کاربری
            if 'username_contains' in criteria:
                username_search = criteria['username_contains'].lower()
                username = (user['username'] or '').lower()
                if username_search not in username:
                    match = False
            
            if match:
                filtered_users.append(user)
        
        return filtered_users
    
    def cleanup_inactive_users(self, days_threshold: int = 30) -> Dict[str, int]:
        """پاکسازی کاربران غیرفعال"""
        import datetime
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
        all_users = self.db.get_all_users()
        
        results = {
            'total_checked': len(all_users),
            'inactive_found': 0,
            'cleaned': 0,
            'errors': 0
        }
        
        for user in all_users:
            try:
                last_activity = datetime.datetime.fromisoformat(user['last_activity'].replace('Z', '+00:00'))
                
                if last_activity < cutoff_date and not user['is_blocked']:
                    results['inactive_found'] += 1
                    
                    # در اینجا می‌توانید تصمیم بگیرید چه کاری انجام دهید
                    # مثلاً بلاک کردن یا ارسال پیام یادآوری
                    # self.db.block_user(user['user_id'])
                    # results['cleaned'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                self.logger.log_system_event("CLEANUP_ERROR", f"خطا در بررسی کاربر {user['user_id']}: {str(e)}")
        
        return results
    
    def generate_user_report(self) -> str:
        """تولید گزارش کامل کاربران"""
        stats = self.get_user_statistics()
        
        if not stats:
            return "📊 **گزارش کاربران**\n\nهیچ کاربری یافت نشد."
        
        report = f"""
📊 **گزارش جامع کاربران**

**👥 آمار کلی:**
• کل کاربران: {stats['total_users']:,}
• کاربران فعال: {stats['active_users']:,} ({stats['activity_rate']}%)
• کاربران بلاک: {stats['blocked_users']:,} ({stats['block_rate']}%)

**📈 آمار فعالیت:**
• کل پیام‌ها: {stats['total_messages']:,}
• میانگین پیام هر کاربر: {stats['avg_messages_per_user']}
• کاربران پرفعالیت: {stats['highly_active_users']:,}

**📅 آمار زمانی:**
• عضویت امروز: {stats['users_today']:,}
• عضویت این هفته: {stats['users_this_week']:,}
• عضویت این ماه: {stats['users_this_month']:,}

**📊 نرخ‌ها:**
• نرخ فعالیت: {stats['activity_rate']}%
• نرخ بلاک: {stats['block_rate']}%

---
📅 تاریخ گزارش: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}
        """
        
        return report

# کلاس کمکی برای عملیات batch
class BatchOperations:
    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
    
    async def batch_block_users(self, user_ids: List[int], reason: str = "عملیات انبوه") -> Dict[str, int]:
        """بلاک انبوه کاربران"""
        results = {'success': 0, 'failed': 0}
        
        for user_id in user_ids:
            try:
                success = self.user_manager.db.block_user(user_id)
                if success:
                    results['success'] += 1
                    self.user_manager.logger.log_admin_action(None, "BATCH_BLOCK", user_id)
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                self.user_manager.logger.log_system_event("BATCH_ERROR", f"خطا در بلاک {user_id}: {str(e)}")
        
        return results
    
    async def batch_unblock_users(self, user_ids: List[int], reason: str = "عملیات انبوه") -> Dict[str, int]:
        """انبلاک انبوه کاربران"""
        results = {'success': 0, 'failed': 0}
        
        for user_id in user_ids:
            try:
                success = self.user_manager.db.unblock_user(user_id)
                if success:
                    results['success'] += 1
                    self.user_manager.logger.log_admin_action(None, "BATCH_UNBLOCK", user_id)
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                self.user_manager.logger.log_system_event("BATCH_ERROR", f"خطا در انبلاک {user_id}: {str(e)}")
        
        return results
