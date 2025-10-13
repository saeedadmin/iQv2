#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اسکریپت مدیریت لاگ‌ها
"""

import argparse
import sys
from pathlib import Path
from logger_system import bot_logger

def show_recent_logs(category="combined", lines=20):
    """نمایش لاگ‌های اخیر"""
    print(f"📋 آخرین {lines} لاگ از {category}:")
    print("-" * 50)
    
    logs = bot_logger.get_recent_logs(category, lines)
    if not logs:
        print("هیچ لاگی یافت نشد")
        return
    
    for log in logs:
        print(log.strip())

def show_error_summary(hours=24):
    """نمایش خلاصه خطاها"""
    print(f"❌ خلاصه خطاهای {hours} ساعت اخیر:")
    print("-" * 50)
    
    summary = bot_logger.get_error_summary(hours)
    if 'error' in summary:
        print(f"خطا: {summary['error']}")
        return
    
    print(f"کل خطاها: {summary['total_errors']}")
    print("\nانواع خطاها:")
    for error_type, count in summary['error_types'].items():
        print(f"  • {error_type}: {count}")
    
    if summary['recent_errors']:
        print("\nآخرین خطاها:")
        for error in summary['recent_errors'][-5:]:
            print(f"  • {error['time']} - {error['message'][:50]}...")

def show_files_info():
    """نمایش اطلاعات فایل‌ها"""
    print("📁 اطلاعات فایل‌های لاگ:")
    print("-" * 50)
    
    info = bot_logger.get_log_files_info()
    if 'error' in info:
        print(f"خطا: {info['error']}")
        return
    
    print(f"تعداد فایل‌ها: {info['files_count']}")
    print(f"حجم کل: {info['total_size_mb']:.2f} MB")
    print("\nفایل‌ها:")
    
    for filename, file_info in info['files'].items():
        print(f"  • {filename}: {file_info['size_mb']:.2f} MB (آخرین تغییر: {file_info['modified']})")

def cleanup_logs(days=30):
    """پاک کردن لاگ‌های قدیمی"""
    print(f"🧹 پاک کردن لاگ‌های قدیمی‌تر از {days} روز...")
    
    count = bot_logger.cleanup_old_logs(days)
    print(f"✅ {count} فایل پاک شد")

def main():
    parser = argparse.ArgumentParser(description='مدیریت لاگ‌های ربات')
    subparsers = parser.add_subparsers(dest='command', help='دستورات موجود')
    
    # دستور نمایش لاگ‌های اخیر
    logs_parser = subparsers.add_parser('logs', help='نمایش لاگ‌های اخیر')
    logs_parser.add_argument('--category', '-c', default='combined', 
                           choices=['combined', 'main', 'errors', 'users', 'admin', 'system'],
                           help='نوع لاگ')
    logs_parser.add_argument('--lines', '-n', type=int, default=20, help='تعداد خطوط')
    
    # دستور خلاصه خطاها
    errors_parser = subparsers.add_parser('errors', help='خلاصه خطاها')
    errors_parser.add_argument('--hours', type=int, default=24, help='ساعات اخیر')
    
    # دستور اطلاعات فایل‌ها
    subparsers.add_parser('files', help='اطلاعات فایل‌ها')
    
    # دستور پاکسازی
    cleanup_parser = subparsers.add_parser('cleanup', help='پاک کردن لاگ‌های قدیمی')
    cleanup_parser.add_argument('--days', '-d', type=int, default=30, help='روزهای قدیمی')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'logs':
            show_recent_logs(args.category, args.lines)
        elif args.command == 'errors':
            show_error_summary(args.hours)
        elif args.command == 'files':
            show_files_info()
        elif args.command == 'cleanup':
            cleanup_logs(args.days)
    except KeyboardInterrupt:
        print("\n❌ عملیات لغو شد")
    except Exception as e:
        print(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
