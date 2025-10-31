#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test script for sports APIs"""

import asyncio
import sys
import os
import io

# حل مشکل encoding برای console ویندوز
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# اضافه کردن مسیر پروژه
sys.path.insert(0, os.path.dirname(__file__))

from handlers.sports import SportsHandler

async def test_apis():
    """تست APIهای ورزشی"""
    sports = SportsHandler()
    
    print("=" * 50)
    print("Testing Sports APIs")
    print("=" * 50)
    
    # تست اخبار فارسی
    print("\n[1] Testing Persian News...")
    news_result = await sports.get_persian_news(limit=5)
    if news_result.get('success'):
        print(f"SUCCESS: Got {news_result['count']} news items")
        for i, news in enumerate(news_result['news'][:2], 1):
            print(f"   {i}. {news['title'][:50]}...")
    else:
        print(f"ERROR: {news_result.get('error')}")
    
    # تست برنامه بازی‌ها
    print("\n[2] Testing La Liga Fixtures...")
    fixtures_result = await sports.get_weekly_fixtures('la_liga')
    if fixtures_result.get('success'):
        print(f"SUCCESS: Found {fixtures_result['count']} scheduled matches")
        for i, match in enumerate(fixtures_result['matches'][:2], 1):
            print(f"   {i}. {match['home_team']} vs {match['away_team']}")
    else:
        print(f"ERROR: {fixtures_result.get('error')}")
        if fixtures_result.get('info'):
            print(f"   INFO: {fixtures_result['info']}")
    
    # تست بازی‌های زنده
    print("\n[3] Testing Live Matches...")
    live_result = await sports.get_live_matches()
    if live_result.get('success'):
        if live_result['count'] > 0:
            print(f"SUCCESS: Found {live_result['count']} live matches")
            for i, match in enumerate(live_result['live_matches'][:2], 1):
                print(f"   {i}. {match['home_team']} {match['score']['home']}-{match['score']['away']} {match['away_team']}")
        else:
            print(f"INFO: {live_result.get('message', 'No live matches')}")
    else:
        print(f"ERROR: {live_result.get('error')}")
        if live_result.get('info'):
            print(f"   INFO: {live_result['info']}")
    
    print("\n" + "=" * 50)
    print("Test Completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_apis())
