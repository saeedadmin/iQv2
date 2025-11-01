#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ماژول مدیریت بخش ورزش
قابلیت‌ها:
- دریافت اخبار ورزشی از منابع فارسی
- دریافت برنامه بازی‌ها (لیگ ایران و اسپانیا)
- نمایش نتایج زنده بازی‌های در جریان
"""

import logging
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SportsHandler:
    """مدیریت اطلاعات ورزشی"""
    
    def __init__(self):
        """مقداردهی handler ورزش"""
        # API-Football (100 req/day - رایگان)
        self.football_api_key = os.getenv('FOOTBALL_DATA_API_KEY', '')
        self.football_api_base = "https://v3.football.api-sports.io"
        
        # RSS Feeds برای اخبار فارسی
        self.varzesh3_rss = "https://www.varzesh3.com/rss/all"
        
        # League IDs (API-Football)
        self.league_ids = {
            'iran': 290,             # Persian Gulf Pro League
            'la_liga': 140,          # La Liga (اسپانیا)
            'premier_league': 39,    # Premier League (انگلیس)
            'bundesliga': 78,        # Bundesliga (آلمان)
            'serie_a': 135,          # Serie A (ایتالیا)
            'ligue_1': 61,           # Ligue 1 (فرانسه)
            'champions_league': 2    # UEFA Champions League
        }
        
        self.timeout = 15
        self.current_season = datetime.now().year
    
    async def get_persian_news(self, limit: int = 10) -> Dict[str, Any]:
        """دریافت اخبار ورزشی از منابع فارسی"""
        try:
            logger.info("🔄 درخواست اخبار ورزشی فارسی...")
            
            # تلاش برای دریافت از RSS Feed
            try:
                feed = feedparser.parse(self.varzesh3_rss)
                
                if not feed.entries:
                    raise Exception("هیچ خبری در RSS Feed یافت نشد")
                
                news_items = []
                for entry in feed.entries[:limit]:
                    news_item = {
                        'title': entry.get('title', 'بدون عنوان'),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', '')
                    }
                    news_items.append(news_item)
                
                logger.info(f"✅ {len(news_items)} خبر دریافت شد")
                return {
                    'success': True,
                    'news': news_items,
                    'count': len(news_items),
                    'source': 'ورزش سه'
                }
            
            except Exception as rss_error:
                logger.error(f"❌ خطا در RSS: {rss_error}")
                
                # Fallback: web scraping ساده
                try:
                    response = requests.get(
                        'https://www.varzesh3.com',
                        timeout=self.timeout,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    
                    if response.status_code == 200:
                        return {
                            'success': True,
                            'news': [{
                                'title': 'اخبار ورزشی',
                                'summary': 'برای دریافت آخرین اخبار به سایت ورزش سه مراجعه کنید',
                                'link': 'https://www.varzesh3.com'
                            }],
                            'count': 1,
                            'source': 'ورزش سه'
                        }
                except Exception as web_error:
                    logger.error(f"❌ خطا در web scraping: {web_error}")
            
            return {
                'success': False,
                'error': 'خطا در دریافت اخبار',
                'news': []
            }
        
        except Exception as e:
            logger.error(f"❌ خطای کلی در get_persian_news: {e}")
            return {
                'success': False,
                'error': str(e),
                'news': []
            }
    
    async def get_weekly_fixtures(self, league: str = 'iran') -> Dict[str, Any]:
        """دریافت برنامه بازی‌های هفتگی (شنبه تا جمعه)"""
        try:
            logger.info(f"🔄 درخواست فیکسچرهای هفتگی {league}...")
            
            league_id = self.league_ids.get(league)
            if not league_id:
                return {
                    'success': False,
                    'error': f'لیگ {league} پشتیبانی نمی‌شود',
                    'matches': []
                }
            
            if not self.football_api_key:
                return {
                    'success': False,
                    'error': 'نیاز به کلید API',
                    'matches': [],
                    'info': 'لطفاً FOOTBALL_DATA_API_KEY را تنظیم کنید'
                }
            
            # محاسبه تاریخ شروع و پایان هفته (شنبه تا جمعه)
            today = datetime.now()
            days_since_saturday = (today.weekday() + 2) % 7
            saturday = today - timedelta(days=days_since_saturday)
            friday = saturday + timedelta(days=6)
            
            date_from = saturday.strftime('%Y-%m-%d')
            date_to = friday.strftime('%Y-%m-%d')
            
            url = f"{self.football_api_base}/fixtures"
            params = {
                'league': str(league_id),
                'season': str(self.current_season),
                'from': date_from,
                'to': date_to
            }
            
            headers = {
                'x-rapidapi-key': self.football_api_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                matches = []
                
                for match in data.get('response', []):
                    fixture = match['fixture']
                    teams = match['teams']
                    goals = match['goals']
                    
                    match_info = {
                        'home_team': teams['home']['name'],
                        'away_team': teams['away']['name'],
                        'date': fixture['date'],
                        'status': fixture['status']['short'],
                        'venue': fixture['venue']['name'] if fixture.get('venue') else 'نامشخص',
                        'score': {
                            'home': goals['home'],
                            'away': goals['away']
                        } if goals['home'] is not None else None
                    }
                    matches.append(match_info)
                
                logger.info(f"✅ {len(matches)} بازی دریافت شد")
                return {
                    'success': True,
                    'matches': matches,
                    'count': len(matches),
                    'league': league,
                    'period': f'{date_from} تا {date_to}'
                }
            
            else:
                logger.error(f"❌ خطای API: {response.status_code} - {response.text[:200]}")
                return {
                    'success': False,
                    'error': f'خطای API: {response.status_code}',
                    'matches': []
                }
        
        except Exception as e:
            logger.error(f"❌ خطا در get_weekly_fixtures: {e}")
            return {
                'success': False,
                'error': str(e),
                'matches': []
            }
    
    async def get_live_matches(self) -> Dict[str, Any]:
        """دریافت بازی‌های زنده (در حال انجام)"""
        try:
            logger.info("🔄 درخواست بازی‌های زنده...")
            
            if not self.football_api_key:
                return {
                    'success': False,
                    'error': 'نیاز به کلید API',
                    'live_matches': [],
                    'info': 'لطفاً FOOTBALL_DATA_API_KEY را تنظیم کنید'
                }
            
            url = f"{self.football_api_base}/fixtures"
            params = {'live': 'all'}  # همه بازی‌های زنده
            
            headers = {
                'x-rapidapi-key': self.football_api_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }
            
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                live_matches = []
                
                # فیلتر برای لیگ‌های مهم (ایران و اروپا)
                important_leagues = [290, 140, 39, 78, 135, 61, 2]  # Iran, La Liga, PL, Bundesliga, Serie A, Ligue 1, UCL
                
                for match in data.get('response', []):
                    league_id = match['league']['id']
                    
                    # فقط لیگ‌های مهم
                    if league_id not in important_leagues:
                        continue
                    
                    fixture = match['fixture']
                    teams = match['teams']
                    goals = match['goals']
                    league = match['league']
                    
                    match_info = {
                        'home_team': teams['home']['name'],
                        'away_team': teams['away']['name'],
                        'league': league['name'],
                        'country': league['country'],
                        'score': {
                            'home': goals['home'] if goals['home'] is not None else 0,
                            'away': goals['away'] if goals['away'] is not None else 0
                        },
                        'minute': fixture['status']['elapsed'],
                        'status': fixture['status']['short']
                    }
                    live_matches.append(match_info)
                
                if live_matches:
                    logger.info(f"✅ {len(live_matches)} بازی زنده یافت شد")
                    return {
                        'success': True,
                        'live_matches': live_matches,
                        'count': len(live_matches)
                    }
                else:
                    logger.info("ℹ️ بازی زنده‌ای یافت نشد")
                    return {
                        'success': True,
                        'live_matches': [],
                        'count': 0,
                        'message': 'در حال حاضر بازی زنده‌ای در جریان نیست'
                    }
            
            else:
                logger.error(f"❌ خطای API: {response.status_code} - {response.text[:200]}")
                return {
                    'success': False,
                    'error': f'خطای API: {response.status_code}',
                    'live_matches': []
                }
        
        except Exception as e:
            logger.error(f"❌ خطا در get_live_matches: {e}")
            return {
                'success': False,
                'error': str(e),
                'live_matches': []
            }
    
    def format_news_message(self, news_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام اخبار"""
        if not news_data.get('success'):
            return f"❌ خطا در دریافت اخبار:\n{news_data.get('error', 'خطای ناشناخته')}"
        
        news_items = news_data.get('news', [])
        if not news_items:
            return "❌ هیچ خبری یافت نشد"
        
        message = f"📰 **آخرین اخبار ورزشی** ({news_data.get('source', '')})\n\n"
        
        for idx, item in enumerate(news_items, 1):
            message += f"{idx}. **{item['title']}**\n"
            if item.get('summary'):
                message += f"   {item['summary']}\n"
            if item.get('link'):
                message += f"   🔗 [مطالعه بیشتر]({item['link']})\n"
            message += "\n"
        
        return message
    
    def format_fixtures_message(self, fixtures_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام برنامه بازی‌ها"""
        if not fixtures_data.get('success'):
            error = fixtures_data.get('error', 'خطای ناشناخته')
            message = f"❌ خطا در دریافت برنامه بازی‌ها:\n{error}"
            
            if fixtures_data.get('info'):
                message += f"\n\n💡 {fixtures_data['info']}"
            
            return message
        
        matches = fixtures_data.get('matches', [])
        if not matches:
            return "❌ هیچ بازی‌ای در این هفته برنامه‌ریزی نشده است"
        
        league_name = {
            'la_liga': 'لالیگا (اسپانیا)',
            'premier_league': 'لیگ برتر انگلیس',
            'iran': 'لیگ برتر ایران'
        }.get(fixtures_data.get('league', ''), fixtures_data.get('league', ''))
        
        message = f"⚽ **برنامه بازی‌های هفتگی {league_name}**\n"
        message += f"📅 {fixtures_data.get('period', '')}\n\n"
        
        for match in matches:
            # تبدیل تاریخ
            try:
                match_date = datetime.fromisoformat(match['date'].replace('Z', '+00:00'))
                date_str = match_date.strftime('%Y/%m/%d %H:%M')
            except:
                date_str = match['date']
            
            message += f"🏟️ **{match['home_team']}** vs **{match['away_team']}**\n"
            message += f"   📅 {date_str}\n"
            
            if match.get('score'):
                message += f"   ⚽ نتیجه: {match['score']['home']} - {match['score']['away']}\n"
            else:
                message += f"   ⏰ برنامه‌ریزی شده\n"
            
            message += "\n"
        
        return message
    
    def format_live_matches_message(self, live_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام بازی‌های زنده"""
        if not live_data.get('success'):
            error = live_data.get('error', 'خطای ناشناخته')
            message = f"❌ خطا در دریافت بازی‌های زنده:\n{error}"
            
            if live_data.get('info'):
                message += f"\n\n💡 {live_data['info']}"
            
            return message
        
        live_matches = live_data.get('live_matches', [])
        if not live_matches:
            return "ℹ️ **بازی زنده‌ای در جریان نیست**\n\n🕐 در حال حاضر هیچ بازی در حال انجام نیست.\n💡 بعداً دوباره بررسی کنید."
        
        message = f"🔴 **بازی‌های زنده** ({len(live_matches)} بازی)\n\n"
        
        for match in live_matches:
            message += f"🏆 **{match['competition']}**\n"
            message += f"🏟️ {match['home_team']} {match['score']['home']} - {match['score']['away']} {match['away_team']}\n"
            message += f"⏱️ دقیقه: {match['minute']}\n\n"
        
        return message
