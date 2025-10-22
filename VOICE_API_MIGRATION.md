# 🎤 مهاجرت از ElevenLabs به Self-Hosted API

## ✅ تغییرات اعمال شده

### 📝 فایل `ai_voice_handler.py`

کد بات شما با موفقیت از **ElevenLabs** به **Self-Hosted API** (Hugging Face Space) مهاجرت کرد!

#### تغییرات اصلی:

1. **حذف وابستگی به ElevenLabs**:
   - پکیج `elevenlabs` دیگر استفاده نمی‌شود
   - به جای آن از `requests` برای HTTP استفاده می‌شود

2. **Endpoint های جدید**:
   - **TTS (Text-to-Speech)**: `POST https://saeedm777-stt.hf.space/tts`
   - **STT (Speech-to-Text)**: `POST https://saeedm777-stt.hf.space/stt`

3. **بهبود محدودیت کاراکتر**:
   - قبلی: 50 کاراکتر (ElevenLabs)
   - جدید: **200 کاراکتر** (Self-Hosted) 🚀

4. **تکنولوژی جدید**:
   - **STT**: OpenAI Whisper (دقت بسیار بالا برای فارسی)
   - **TTS**: Coqui TTS با مدل فارسی (کیفیت عالی)

---

## 🔧 نحوه کار

### Speech-to-Text (STT)
```python
# فایل صوتی را به API ارسال می‌کند
with open(audio_file_path, 'rb') as audio_file:
    files = {'file': audio_file}
    response = requests.post(
        f"{self.api_url}/stt",
        files=files,
        timeout=60
    )

# متن را از JSON دریافت می‌کند
result = response.json()
text = result.get('text', '')
```

### Text-to-Speech (TTS)
```python
# متن را به API ارسال می‌کند
response = requests.post(
    f"{self.api_url}/tts",
    json={"text": text},
    timeout=60
)

# فایل صوتی WAV را دریافت می‌کند
with open(audio_path, 'wb') as f:
    f.write(response.content)
```

---

## 🚀 مزایای جدید

### ✅ مزایا:
1. **100% رایگان**: دیگر نیازی به API key یا پرداخت نیست
2. **کیفیت بهتر برای فارسی**: Whisper و Coqui بهینه شده برای فارسی
3. **محدودیت کاراکتر بیشتر**: 200 کاراکتر به جای 50
4. **کنترل کامل**: شما مالک سرویس خود هستید
5. **بدون محدودیت روزانه سخت**: فقط محدودیت نرم‌افزاری بات (10 درخواست/روز برای کاربران عادی)

### ⚠️ نکات مهم:
1. **Hugging Face Spaces رایگان "می‌خوابد"** (sleep) پس از 48 ساعت عدم استفاده
   - اولین درخواست بعد از sleep حدود 30-60 ثانیه طول می‌کشد (cold start)
   - درخواست‌های بعدی سریع هستند

2. **Timeout افزایش یافته**: به 60 ثانیه برای پشتیبانی از cold start

3. **فرمت خروجی**: فایل‌های صوتی به صورت WAV ذخیره می‌شوند (به جای MP3)

---

## 📊 مقایسه قبل/بعد

| ویژگی | ElevenLabs (قبل) | Self-Hosted (جدید) |
|--------|------------------|--------------------|
| هزینه | پولی (محدودیت رایگان) | **100% رایگان** ✅ |
| کیفیت فارسی TTS | متوسط | **عالی** ✅ |
| کیفیت فارسی STT | خوب | **عالی** ✅ |
| محدودیت کاراکتر | 50 | **200** ✅ |
| نیاز به API Key | بله ❌ | خیر ✅ |
| Cold Start | سریع | 30-60s (فقط بعد از sleep) |
| فرمت خروجی | MP3 | WAV |

---

## 🔄 آینده

اگر ترافیک بات زیاد شد، می‌توانید:
1. به Hugging Face Pro ارتقا دهید (برای جلوگیری از sleep)
2. یا به Oracle Cloud Always Free مهاجرت کنید (قدرت بیشتر، همیشه روشن)

---

## ✅ وضعیت نهایی

- ✅ فایل `ai_voice_handler.py` به‌روزرسانی شد
- ✅ API Endpoint ها تنظیم شدند: `https://saeedm777-stt.hf.space`
- ✅ تست import موفق بود
- ✅ Hugging Face Space آماده و در حال اجرا است

**بات شما آماده استفاده از سرویس جدید است!** 🎉

فقط کافیست بات را restart کنید تا تغییرات اعمال شوند.
