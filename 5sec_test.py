#!/usr/bin/env python3
# یک خطی ترین تست - فقط کد پاسخ رو نشون میده
import requests
resp = requests.post("https://iqv2.onrender.com/webhook/ff17baeb-3182-41c4-b60a-e6159b02023b/webhook", json={"test":"quick"})
print(f"کد پاسخ: {resp.status_code}")
if resp.status_code == 200: print("🎉 SUCCESS! ورکفلو فعال!") 
elif resp.status_code == 403: print("❌ 403 - ورکفلو غیرفعال")
else: print(f"❓ کد غیرمعمول: {resp.status_code}")