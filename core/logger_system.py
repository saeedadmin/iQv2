#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
سیستم لاگ پیشرفته برای ربات تلگرام
مدیریت کامل خطاها و رویدادها با فایل‌های جداگانه
"""

import logging
import os
import datetime
import traceback
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

class BotLogger:
    def __init__(self, log_dir: str = "logs"):
        """مقداردهی سیستم لاگ"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # ایجاد لاگرهای مختلف
        self.main_logger = self._create_logger('main', 'bot_main.log')
        self.error_logger = self._create_logger('error', 'bot_errors.log')
        self.user_logger = self._create_logger('user', 'bot_users.log')
        self.admin_logger = self._create_logger('admin', 'bot_admin.log')
        self.system_logger = self._create_logger('system', 'bot_system.log')
        
        # فایل لاگ کلی
        self.combined_log_file = self.log_dir / "bot_combined.log"
        
        self.main_logger.info("🚀 سیستم لاگ راه‌اندازی شد")
    
    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """ایجاد لاگر با تنظیمات خاص"""
        logger = logging.getLogger(f"bot_{name}")
        logger.setLevel(logging.DEBUG)
        
        # جلوگیری از duplicate handler ها
        if logger.handlers:
            return logger
        
        # فرمت لاگ
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # فایل handler با rotation
        log_file = self.log_dir / filename
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Console handler برای خطاهای مهم
        if name in ['error', 'main']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        logger.addHandler(file_handler)
        return logger
    
    def log_info(self, message: str, category: str = "main"):
        """لاگ اطلاعات عمومی"""
        logger = getattr(self, f"{category}_logger", self.main_logger)
        logger.info(message)
        self._write_combined_log("INFO", category, message)
    
    def log_warning(self, message: str, category: str = "main"):
        """لاگ هشدار"""
        logger = getattr(self, f"{category}_logger", self.main_logger)
        logger.warning(message)
        self._write_combined_log("WARNING", category, message)
    
    def log_error(self, message: str, error: Optional[Exception] = None, category: str = "error"):
        """لاگ خطا با جزئیات کامل"""
        error_details = ""
        if error:
            error_details = f"\n📋 Exception: {type(error).__name__}: {str(error)}"
            error_details += f"\n📍 Traceback:\n{traceback.format_exc()}"
        
        full_message = f"{message}{error_details}"
        
        self.error_logger.error(full_message)
        self._write_combined_log("ERROR", category, message)
        
        # سیستم اطلاعات در زمان خطا
        system_info = self._get_system_snapshot()
        self.system_logger.error(f"System snapshot at error: {system_info}")
    
    def log_user_action(self, user_id: int, action: str, details: str = ""):
        """لاگ عملیات کاربر"""
        message = f"User {user_id} | Action: {action}"
        if details:
            message += f" | Details: {details}"
        
        self.user_logger.info(message)
        self._write_combined_log("USER", "user", message)
    
    def log_admin_action(self, admin_id: int, action: str, target: str = "", details: str = ""):
        """لاگ عملیات ادمین"""
        message = f"Admin {admin_id} | Action: {action}"
        if target:
            message += f" | Target: {target}"
        if details:
            message += f" | Details: {details}"
        
        self.admin_logger.info(message)
        self._write_combined_log("ADMIN", "admin", message)
    
    def log_system_event(self, event: str, details: str = ""):
        """لاگ رویدادهای سیستم"""
        message = f"Event: {event}"
        if details:
            message += f" | Details: {details}"
        
        self.system_logger.info(message)
        self._write_combined_log("SYSTEM", "system", message)
    
    def _write_combined_log(self, level: str, category: str, message: str):
        """نوشتن در فایل لاگ کلی"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp} | {level:8} | {category:8} | {message}\n"
            
            with open(self.combined_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # جلوگیری از لوپ خطا
    
    def _get_system_snapshot(self) -> Dict[str, Any]:
        """عکس فوری از وضعیت سیستم"""
        try:
            return {
                'timestamp': datetime.datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids())
            }
        except Exception:
            return {'error': 'Could not get system snapshot'}
    
    def get_recent_logs(self, category: str = "combined", lines: int = 50) -> list:
        """دریافت لاگ‌های اخیر از فایل"""
        try:
            if category == "combined":
                log_file = self.combined_log_file
            else:
                log_file = self.log_dir / f"bot_{category}.log"
            
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if all_lines else []
        
        except Exception as e:
            self.log_error(f"خطا در خواندن لاگ {category}", e)
            return []
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """خلاصه خطاهای اخیر"""
        try:
            error_logs = self.get_recent_logs("errors", 200)
            
            # فیلتر بر اساس زمان
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            recent_errors = []
            error_types = {}
            
            for log_line in error_logs:
                try:
                    # پارس خط لاگ
                    parts = log_line.strip().split(' | ', 3)
                    if len(parts) >= 4:
                        timestamp_str = parts[0]
                        log_time = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if log_time >= cutoff_time:
                            error_msg = parts[3]
                            recent_errors.append({
                                'time': timestamp_str,
                                'message': error_msg
                            })
                            
                            # شمارش نوع خطاها
                            error_type = error_msg.split(':')[0] if ':' in error_msg else 'Unknown'
                            error_types[error_type] = error_types.get(error_type, 0) + 1
                
                except Exception:
                    continue
            
            return {
                'total_errors': len(recent_errors),
                'error_types': error_types,
                'recent_errors': recent_errors[-10:],  # آخرین 10 خطا
                'period_hours': hours
            }
        
        except Exception as e:
            self.log_error("خطا در تهیه خلاصه خطاها", e)
            return {'error': str(e)}
    
    def cleanup_old_logs(self, days: int = 30):
        """پاک کردن لاگ‌های قدیمی"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            cleaned_count = 0
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned_count += 1
            
            self.log_system_event("LOG_CLEANUP", f"پاک شد {cleaned_count} فایل لاگ قدیمی")
            return cleaned_count
        
        except Exception as e:
            self.log_error("خطا در پاک کردن لاگ‌های قدیمی", e)
            return 0
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """اطلاعات فایل‌های لاگ"""
        try:
            files_info = {}
            total_size = 0
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.is_file():
                    size = log_file.stat().st_size
                    total_size += size
                    
                    files_info[log_file.name] = {
                        'size_mb': round(size / (1024*1024), 2),
                        'modified': datetime.datetime.fromtimestamp(
                            log_file.stat().st_mtime
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            return {
                'files': files_info,
                'total_size_mb': round(total_size / (1024*1024), 2),
                'files_count': len(files_info)
            }
        
        except Exception as e:
            self.log_error("خطا در دریافت اطلاعات فایل‌های لاگ", e)
            return {'error': str(e)}

# نمونه سراسری
bot_logger = BotLogger()