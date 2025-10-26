# سیستم Backup و Restore دیتابیس

## 📋 **معرفی**

این سیستم backup خودکار برای حفظ داده‌های ربات در محیط Koyeb طراحی شده است.

## 🎯 **ویژگی‌ها**

### **1. Persistent Storage**
- دیتابیس SQLite در مسیر `/tmp/` ذخیره می‌شود
- در محیط Koyeb، این مسیر persistent است
- با هر restart، داده‌ها حفظ می‌شوند

### **2. Automatic Backup**
- **Startup**: بازگردانی backup در زمان شروع ربات
- **Periodically**: Backup هر 6 ساعت یکبار
- **Admin**: Backup دستی از طریق پنل ادمین

### **3. Admin Interface**
- دکمه "💾 Backup" در منوی سیستم
- نمایش آمار دیتابیس
- امکان backup دستی و refresh

### **4. Fallback System**
- اگر persistent storage در دسترس نباشد، به in-memory fallback می‌کند
- تست خودکار persistence قبل از استفاده
- لاگ‌گیری کامل برای debugging

## 🔧 **نحوه کار**

### **Database Location**
```
Production: /tmp/bot_database.db
Backup File: /tmp/bot_database.db.backup
```

### **Startup Sequence**
1. بررسی و ایجاد دیتابیس persistent
2. تلاش برای restore از backup موجود
3. اجرای migrationها
4. ایجاد backup جدید

### **Background Tasks**
- `auto_unblock_task`: هر 1 دقیقه - آنبلاک خودکار
- `cleanup_tracking_task`: هر 1 ساعت - پاک‌سازی tracking
- `backup_task`: هر 6 ساعت - backup خودکار

## 📊 **Admin Commands**

### **Backup Interface**
- ورود به پنل ادمین → سیستم → 💾 Backup
- مشاهده آمار دیتابیس
- ایجاد backup دستی
- refresh برای بروزرسانی آمار

## 🚨 **Troubleshooting**

### **Database Errors**
- بررسی لاگ‌ها برای persistence errors
- سیستم خودکار fallback به in-memory
- دسترسی manual backup از admin panel

### **Missing Data**
- سیستم خودکار restore در startup
- backup files در `/tmp/` directory
- بررسی manual backup در admin panel

## ✅ **Benefits**

1. **Data Persistence**: داده‌ها با هر restart حفظ می‌شوند
2. **Automatic Recovery**: بازگردانی خودکار در startup
3. **Admin Control**: کنترل کامل توسط ادمین
4. **Monitoring**: آمار دیتابیس در admin panel
5. **Safety**: backup خودکار و دستی

---

**نویسنده**: MiniMax Agent  
**تاریخ**: 2025-10-26  
**نسخه**: 1.0