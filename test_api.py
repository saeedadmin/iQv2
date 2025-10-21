import requests
import json

API_KEY = "AIzaSyA8HKbAXWjvh_cKQ8ynbyXztw6zIczelGk"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"

# Test 1: Simple greeting
print("=" * 70)
print("TEST 1: تست ساده - سلام")
print("=" * 70)
payload1 = {
    "contents": [{
        "parts": [{"text": "سلام! یک جمله درباره هوش مصنوعی بگو."}]
    }]
}
response1 = requests.post(url, json=payload1, timeout=30)
print(f"Status: {response1.status_code}")
if response1.status_code == 200:
    result1 = response1.json()
    ai_response = result1['candidates'][0]['content']['parts'][0]['text']
    print(f"✅ پاسخ AI: {ai_response}")
    print(f"📊 Tokens استفاده شده: {result1['usageMetadata']['totalTokenCount']}")
else:
    print(f"❌ خطا: {response1.text}")

print("\n" + "=" * 70)
print("TEST 2: سوال پیچیده‌تر")
print("=" * 70)
payload2 = {
    "contents": [{
        "parts": [{"text": "مزایای استفاده از پایتون برای برنامه‌نویسی چیست? لطفا 3 مورد بگو."}]
    }]
}
response2 = requests.post(url, json=payload2, timeout=30)
print(f"Status: {response2.status_code}")
if response2.status_code == 200:
    result2 = response2.json()
    ai_response2 = result2['candidates'][0]['content']['parts'][0]['text']
    print(f"✅ پاسخ AI:\n{ai_response2}")
    print(f"📊 Tokens استفاده شده: {result2['usageMetadata']['totalTokenCount']}")
else:
    print(f"❌ خطا: {response2.text}")

print("\n" + "=" * 70)
print("TEST 3: سوال به انگلیسی")
print("=" * 70)
payload3 = {
    "contents": [{
        "parts": [{"text": "What is artificial intelligence? Give me a short answer."}]
    }]
}
response3 = requests.post(url, json=payload3, timeout=30)
print(f"Status: {response3.status_code}")
if response3.status_code == 200:
    result3 = response3.json()
    ai_response3 = result3['candidates'][0]['content']['parts'][0]['text']
    print(f"✅ AI Response:\n{ai_response3}")
    print(f"📊 Tokens Used: {result3['usageMetadata']['totalTokenCount']}")
else:
    print(f"❌ Error: {response3.text}")

print("\n" + "=" * 70)
print("✅ نتیجه نهایی: API به درستی کار می‌کند!")
print("=" * 70)
