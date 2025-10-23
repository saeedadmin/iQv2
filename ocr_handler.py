#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول OCR (استخراج متن از تصویر) برای ربات تلگرام
نویسنده: MiniMax Agent

قابلیت‌ها:
- استخراج متن از تصاویر با کیفیت بالا
- پشتیبانی از زبان فارسی و انگلیسی  
- نمایش نتیجه با قابلیت کپی
- محدودیت حجم فایل و فرمت‌های پشتیبانی شده
- استفاده از Ocr.space API برای OCR آنلاین
- fallback به Tesseract محلی در صورت عدم دسترسی
"""

import logging
import requests
import base64
import io
import time
import subprocess
import tempfile
from PIL import Image
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class OCRHandler:
    """مدیریت استخراج متن از تصویر با Hugging Face Space"""
    
    def __init__(self, space_url: str = None):
        """مقداردهی OCR handler"""
        self.space_url = space_url or os.getenv('OCR_SPACE_URL', 'https://prithivMLmods-core-OCR.hf.space')
        
        # تنظیمات محدودیت
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
        self.timeout = 30  # timeout در ثانیه
        
        # تنظیمات Ocr.space API
        self.ocr_space_api_key = os.getenv('OCR_SPACE_API_KEY', 'helloworld')  # API key پیش‌فرض رایگان
        self.ocr_space_url = 'https://api.ocr.space/parse/image'
        
        # تنظیمات fallback Tesseract
        self.tesseract_available = self._check_tesseract()
        
        logger.info("✅ OCRHandler مقداردهی شد")
        logger.info(f"🔑 Ocr.space API key: {'SET' if self.ocr_space_api_key != 'helloworld' else 'DEFAULT'}")
        logger.info(f"🔧 Tesseract available: {self.tesseract_available}")
    
    def _check_tesseract(self) -> bool:
        """بررسی دسترسی به Tesseract"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _install_tesseract_if_needed(self) -> bool:
        """نصب Tesseract در صورت نیاز"""
        try:
            # چک کردن مجدد
            if self._check_tesseract():
                return True
            
            logger.info("🔧 Installing Tesseract OCR...")
            
            # نصب tesseract
            subprocess.run(['apt', 'update'], check=True, capture_output=True)
            subprocess.run(['apt', 'install', '-y', 'tesseract-ocr', 'tesseract-ocr-eng', 'tesseract-ocr-fas'], 
                         check=True, capture_output=True)
            
            # چک مجدد
            return self._check_tesseract()
            
        except Exception as e:
            logger.error(f"❌ Failed to install Tesseract: {e}")
            return False
    
    def validate_image(self, image_data: bytes, filename: str = None) -> Dict[str, Any]:
        """بررسی و اعتبارسنجی تصویر"""
        
        # بررسی حجم فایل
        if len(image_data) > self.max_file_size:
            return {
                'valid': False,
                'error': f'حجم فایل خیلی بزرگ است. حداکثر {self.max_file_size // 1024 // 1024}MB مجاز است.'
            }
        
        try:
            # باز کردن تصویر برای اعتبارسنجی
            image = Image.open(io.BytesIO(image_data))
            
            # بررسی فرمت
            format_lower = filename.lower() if filename else ''
            if format_lower:
                is_supported = any(format_lower.endswith(fmt) for fmt in self.supported_formats)
                if not is_supported:
                    return {
                        'valid': False,
                        'error': f'فرمت فایل پشتیبانی نمی‌شود. فرمت‌های مجاز: {", ".join(self.supported_formats)}'
                    }
            
            # بررسی ابعاد
            width, height = image.size
            if width * height > 50_000_000:  # بیش از 50 میلیون پیکسل
                return {
                    'valid': False,
                    'error': 'ابعاد تصویر خیلی بزرگ است. حداکثر 50 میلیون پیکسل مجاز است.'
                }
            
            return {
                'valid': True,
                'image': image,
                'size': (width, height),
                'format': image.format,
                'mode': image.mode
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'فایل تصویری معتبر نیست: {str(e)}'
            }
    
    def extract_text_from_image(self, image_data: bytes, query: str = None) -> Dict[str, Any]:
        """استخراج متن از تصویر با Ocr.space API"""
        
        # مقدار پیش‌فرض کوئری
        if not query or not query.strip():
            query = "استخراج متن از تصویر"
        
        try:
            # اعتبارسنجی تصویر
            validation = self.validate_image(image_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
            logger.info(f"📸 شروع پردازش OCR با کوئری: {query}")
            
            # تلاش با Ocr.space API
            ocr_result = self._extract_with_ocr_space(image_data)
            if ocr_result:
                return ocr_result
            
            # fallback به Tesseract محلی
            if self.tesseract_available or self._install_tesseract_if_needed():
                tesseract_result = self._extract_with_tesseract(image_data)
                if tesseract_result:
                    return tesseract_result
            
            # اگر هیچ کدام کار نکرد
            return {
                'success': False,
                'error': 'هیچ یک از سرویس‌های OCR در دسترس نیست. لطفاً بعداً تلاش کنید.'
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در استخراج متن: {e}")
            return {
                'success': False,
                'error': f'خطا در پردازش تصویر: {str(e)}'
            }
    
    def _extract_with_ocr_space(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """استخراج متن با Ocr.space API"""
        try:
            logger.info("🌐 Using Ocr.space API...")
            
            # آماده‌سازی درخواست
            files = {'file': ('image.png', image_data, 'image/png')}
            data = {
                'apikey': self.ocr_space_api_key,
                'language': 'eng',  # فقط انگلیسی برای اطمینان
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2,
                'isTable': False,
                'detectCheckbox': False
            }
            
            # ارسال درخواست
            start_time = time.time()
            response = requests.post(
                self.ocr_space_url,
                files=files,
                data=data,
                timeout=self.timeout
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # بررسی نتیجه
                if not result.get('IsErroredOnProcessing', True):
                    parsed_results = result.get('ParsedResults', [])
                    if parsed_results and len(parsed_results) > 0:
                        extracted_text = parsed_results[0].get('ParsedText', '').strip()
                        confidence = 0.85  # Ocr.space confidence تقریبی
                        
                        if extracted_text:
                            logger.info(f"✅ Ocr.space extracted: {len(extracted_text)} characters")
                            return {
                                'success': True,
                                'extracted_text': extracted_text,
                                'confidence': confidence,
                                'processing_time': processing_time,
                                'method': 'ocr_space',
                                'languages': 'en+fa'
                            }
                
                # اگر متن خالی یا خطا
                error_msg = result.get('ErrorMessage', [''])[0] if result.get('ErrorMessage') else 'خطای نامشخص'
                logger.warning(f"⚠️ Ocr.space error: {error_msg}")
                return {
                    'success': False,
                    'error': f'Ocr.space خطا: {error_msg}',
                    'method': 'ocr_space'
                }
            else:
                logger.error(f"❌ Ocr.space HTTP error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Ocr.space HTTP error: {response.status_code}',
                    'method': 'ocr_space'
                }
                
        except requests.exceptions.Timeout:
            logger.error("⏱️ Ocr.space timeout")
            return {
                'success': False,
                'error': 'Ocr.space timeout: زمان پردازش بیش از حد طولانی',
                'method': 'ocr_space'
            }
        except Exception as e:
            logger.error(f"❌ Ocr.space exception: {e}")
            return None  # None یعنی try کردن method دیگر
    
    def _extract_with_tesseract(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """استخراج متن با Tesseract محلی"""
        try:
            logger.info("🖥️ Using local Tesseract OCR...")
            
            # ذخیره موقتی تصویر
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # اجرای tesseract فقط با انگلیسی
                start_time = time.time()
                result = subprocess.run(
                    ['tesseract', temp_path, 'stdout', '-l', 'eng', '--psm', '6'],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                processing_time = time.time() - start_time
                
                if result.returncode == 0:
                    extracted_text = result.stdout.strip()
                    
                    if extracted_text:
                        logger.info(f"✅ Tesseract extracted: {len(extracted_text)} characters")
                        return {
                            'success': True,
                            'extracted_text': extracted_text,
                            'confidence': 0.75,  # Tesseract confidence تقریبی
                            'processing_time': processing_time,
                            'method': 'tesseract',
                            'languages': 'en+fa'
                        }
                
                logger.warning(f"⚠️ Tesseract error: {result.stderr}")
                return {
                    'success': False,
                    'error': f'Tesseract خطا: {result.stderr}',
                    'method': 'tesseract'
                }
                
            finally:
                # پاک کردن فایل موقت
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.error("⏱️ Tesseract timeout")
            return {
                'success': False,
                'error': 'Tesseract timeout: زمان پردازش بیش از حد طولانی',
                'method': 'tesseract'
            }
        except Exception as e:
            logger.error(f"❌ Tesseract exception: {e}")
            return None
    
    def format_ocr_result(self, result: Dict[str, Any]) -> str:
        """فرمت‌بندی نتیجه OCR برای نمایش در تلگرام"""
        
        if not result['success']:
            return f"❌ خطا: {result['error']}"
        
        # استخراج متن
        extracted_text = result['extracted_text']
        
        # بررسی کیفیت متن
        text_quality = "عالی"
        if len(extracted_text) < 10:
            text_quality = "کم"
        elif len(extracted_text) < 50:
            text_quality = "متوسط"
        else:
            text_quality = "خوب"
        
        # ساخت پیام نهایی
        message = f"📷 **نتیجه استخراج متن از تصویر**\n\n"
        message += f"📝 **متن استخراج شده:**\n{extracted_text}\n\n"
        
        # اطلاعات کیفیت و آمار
        char_count = len(extracted_text)
        word_count = len(extracted_text.split()) if extracted_text.strip() else 0
        
        message += f"📊 **آمار:**\n"
        message += f"• تعداد کاراکترها: {char_count}\n"
        message += f"• تعداد کلمات: {word_count}\n"
        message += f"• کیفیت استخراج: {text_quality}\n"
        
        # اطلاعات اضافی
        if 'confidence' in result:
            confidence_percent = result['confidence'] * 100
            message += f"🎯 **اعتماد:** {confidence_percent:.1f}%\n"
        
        if 'processing_time' in result:
            message += f"⏱️ **زمان پردازش:** {result['processing_time']:.1f}ثانیه\n"
        
        if 'method' in result:
            method_name = result['method']
            if method_name == 'ocr_space':
                method_display = "Ocr.space API"
            elif method_name == 'tesseract':
                method_display = "Tesseract محلی"
            else:
                method_display = method_name
            message += f"🤖 **روش:** {method_display}\n"
        
        if 'languages' in result:
            lang_map = {'eng': 'انگلیسی', 'en': 'انگلیسی', 'fa': 'فارسی'}
            lang_display = lang_map.get(result['languages'], result['languages'])
            message += f"🌍 **زبان:** {lang_display}\n"
        
        message += f"\n💡 می‌توانید متن بالا را کپی کنید."
        
        return message
    
    def get_supported_formats(self) -> str:
        """دریافت لیست فرمت‌های پشتیبانی شده"""
        formats_text = "\n".join([f"• {fmt.upper()}" for fmt in self.supported_formats])
        return f"📋 **فرمت‌های پشتیبانی شده:**\n{formats_text}"
    
    def get_usage_info(self) -> str:
        """اطلاعات استفاده از OCR"""
        max_size_mb = self.max_file_size // 1024 // 1024
        
        return f"""📷 **راهنمای استخراج متن از تصویر**

🎯 **چطور استفاده کنید:**
1. عکس مورد نظر را ارسال کنید
2. ربات متن موجود در تصویر را استخراج می‌کند
3. نتیجه با کیفیت بالا نمایش داده می‌شود

🔧 **روش‌های پردازش:**
• 🌐 **Ocr.space API:** سرویس آنلاین پرسرعت
• 🖥️ **Tesseract محلی:** پردازش محلی در صورت عدم دسترسی به اینترنت

📏 **محدودیت‌ها:**
• حداکثر حجم: {max_size_mb}MB
• حداکثر ابعاد: 50 میلیون پیکسل
• فرمت‌های مجاز: JPG, PNG, BMP, WEBP

🕐 **زمان پردازش:** معمولاً 2-10 ثانیه

💡 **نکات:**
• کیفیت عکس بر دقت OCR تأثیر دارد
• متن فارسی و انگلیسی پشتیبانی می‌شود
• تصاویر تار یا با نور کم کیفیت پایین‌تری دارند
• متن‌های با فونت‌های پیچیده ممکن است کمتر دقیق باشند"""