#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

API_KEY = "AIzaSyA8HKbAXWjvh_cKQ8ynbyXztw6zIczelGk"

def test_gemini_api(question, test_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": question}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print(f"{'='*70}")
        print(f"سوال: {question}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result['candidates'][0]['content']['parts'][0]['text']
            tokens = result['usageMetadata']['totalTokenCount']
            
            print(f"\n✅ SUCCESS!")
            print(f"\nپاسخ AI:")
            print(f"{'-'*70}")
            print(ai_text)
            print(f"{'-'*70}")
            print(f"📊 Tokens: {tokens}")
            return True
        else:
            print(f"\n❌ FAILED!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return False

# Run tests
print("\n" + "="*70)
print("🧪 GOOGLE GEMINI API TEST SUITE")
print("="*70)

test1 = test_gemini_api("سلام! یک جمله کوتاه درباره هوش مصنوعی بگو.", "تست فارسی ساده")
test2 = test_gemini_api("مزایای پایتون را در 3 خط توضیح بده.", "تست فارسی پیچیده")
test3 = test_gemini_api("What is AI? Short answer please.", "تست انگلیسی")

print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)
print(f"Test 1 (فارسی ساده): {'✅ PASSED' if test1 else '❌ FAILED'}")
print(f"Test 2 (فارسی پیچیده): {'✅ PASSED' if test2 else '❌ FAILED'}")
print(f"Test 3 (انگلیسی): {'✅ PASSED' if test3 else '❌ FAILED'}")

if test1 and test2 and test3:
    print("\n🎉 همه تست‌ها موفق! API آماده استفاده است.")
else:
    print("\n⚠️ برخی تست‌ها شکست خوردند!")
    
print("="*70 + "\n")
