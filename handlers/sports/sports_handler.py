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
from typing import Dict, Any, List, Optional
import os
from bs4 import BeautifulSoup
import pytz
from dateutil import parser

logger = logging.getLogger(__name__)

class SportsHandler:
    """مدیریت اطلاعات ورزشی"""
    
    def __init__(self, db_manager = None):
        """مقداردهی handler ورزش"""
        self.db = db_manager
        # API-Football (100 req/day - رایگان)
        self.api_keys = [
            os.getenv('FOOTBALL_DATA_API_KEY', ''),
            os.getenv('FOOTBALL_DATA_API_KEY_2', '')
        ]
        # حذف کلیدهای خالی
        self.api_keys = [key for key in self.api_keys if key]

        self.football_api_base = "https://v3.football.api-sports.io"
        self.current_api_index = 0
        self.football_api_key = self.api_keys[0] if self.api_keys else ''

        # وضعیت محدودیت برای هر کلید
        self.api_limits = {i: {'used': 0, 'limit': 100, 'exhausted': False} for i in range(len(self.api_keys))}

        if not self.api_keys:
            logger.warning("⚠️ هیچ کلید API برای SportsHandler تنظیم نشده است")
        
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

        self.league_display_names = {
            'iran': '🇮🇷 لیگ برتر ایران',
            'la_liga': '🇪🇸 لالیگا (اسپانیا)',
            'premier_league': '🏴 لیگ برتر (انگلیس)',
            'serie_a': '🇮🇹 سری آ (ایتالیا)',
            'bundesliga': '🇩🇪 بوندسلیگا (آلمان)',
            'ligue_1': '🇫🇷 لیگ یک (فرانسه)',
            'champions_league': '🏆 لیگ قهرمانان اروپا'
        }

        self.league_order = ['iran', 'la_liga', 'premier_league', 'serie_a', 'bundesliga', 'ligue_1']
        
        self.timeout = 15
        self.current_season = self._get_current_season()
        self.team_cache: Dict[str, Dict[str, Any]] = {}
        self.season_cache: Dict[int, Dict[str, Any]] = {}
        self.league_meta_cache: Dict[int, Dict[str, Any]] = {}

    def _get_current_season(self) -> int:
        """محاسبه فصل جاری برای لیگ‌ها (لیگ‌های اروپایی از تابستان آغاز می‌شوند)"""
        now = datetime.now()
        return now.year - 1 if now.month < 7 else now.year

    async def _get_league_season_metadata(self, league_id: int) -> List[Dict[str, Any]]:
        """دریافت اطلاعات فصول یک لیگ همراه با پوشش"""
        cached = self.league_meta_cache.get(league_id)
        if cached:
            fetched_at: datetime = cached['fetched_at']
            if (datetime.now() - fetched_at).total_seconds() <= 12 * 3600:
                return cached['seasons']

        if not self.api_keys:
            return []

        for api_index in range(len(self.api_keys)):
            if self.api_limits[api_index]['exhausted']:
                continue

            current_key = self.api_keys[api_index]
            self.current_api_index = api_index

            headers = {
                'x-rapidapi-key': current_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }

            try:
                response = requests.get(
                    f"{self.football_api_base}/leagues",
                    headers=headers,
                    params={'id': league_id},
                    timeout=self.timeout
                )

                if not self.handle_api_response(response):
                    self.api_limits[self.current_api_index]['exhausted'] = True
                    continue

                if response.status_code == 200:
                    data = response.json()
                    seasons = []
                    try:
                        league_info = data.get('response', [])[0]
                        seasons = league_info.get('seasons', []) if league_info else []
                    except Exception:
                        seasons = []

                    if seasons:
                        seasons_sorted = sorted(seasons, key=lambda s: s.get('year', 0), reverse=True)
                        self.league_meta_cache[league_id] = {
                            'seasons': seasons_sorted,
                            'fetched_at': datetime.now()
                        }
                        return seasons_sorted
                    else:
                        logger.warning(f"⚠️ هیچ فصلی برای لیگ {league_id} یافت نشد")
                else:
                    logger.warning(f"❌ خطا در دریافت اطلاعات لیگ {league_id} (کد {response.status_code})")

            except Exception as e:
                logger.error(f"❌ استثنا در دریافت اطلاعات لیگ {league_id}: {e}")
                continue

        return []

    def get_current_api_key(self) -> str:
        """دریافت کلید API فعلی با بررسی محدودیت"""
        if not self.api_keys:
            return ''
        
        # پیدا کردن اولین کلیدی که به محدودیت نخورده
        for i in range(len(self.api_keys)):
            if not self.api_limits[i]['exhausted']:
                return self.api_keys[i]
        
        return ''  # همه کلیدها به محدودیت خوردن
    
    def _invalidate_team_cache(self, league_key: Optional[str] = None) -> None:
        if league_key:
            self.team_cache.pop(league_key, None)
        else:
            self.team_cache.clear()

    def handle_api_response(self, response):
        """بررسی پاسخ API و مدیریت محدودیت"""
        if response.status_code == 429:  # Too Many Requests
            # علامت گذاری کلید فعلی به عنوان محدودیت خورده
            self.api_limits[self.current_api_index]['exhausted'] = True
            logger.warning(f"API Key {self.current_api_index} به محدودیت خورد")
            return False  # خطای محدودیت
        
        elif response.status_code == 200:
            # بررسی هدر مصرف
            try:
                remaining = response.headers.get('x-ratelimit-requests-remaining', '100')
                remaining = int(remaining)
                
                if remaining <= 5:  # نزدیک به محدودیت
                    self.api_limits[self.current_api_index]['exhausted'] = True
                    logger.warning(f"API Key {self.current_api_index} نزدیک به محدودیت (موجود: {remaining})")
                    return False
                
                return True  # موفقیت
            except:
                return True  # اگر هدر نبود، فرض موفقیت
        
        return True  # سایر خطاها محدودیت نیست
    
    def get_rate_limit_message(self) -> str:
        """پیام مناسب برای محدودیت مصرف"""
        exhausted_count = sum(1 for limit in self.api_limits.values() if limit['exhausted'])
        
        if exhausted_count == len(self.api_keys):
            return "❌ **محدودیت API مصرف شد!**\n\n📊 هر دو کلید API به محدودیت روزانه (100 درخواست) رسیدن.\n\n🔄 لطفاً فردا دوباره تلاش کنید.\n\n⏰ محدودیت‌ها در نیمه‌شب به وقت UTC ریست میشن."
        else:
            return "❌ **یک کلید API به محدودیت رسید!**\n\n🔄 در حال استفاده از کلید دیگر..."
    
    async def get_league_teams(self, league_key: str) -> Dict[str, Any]:
        """دریافت تیم‌های یک لیگ با استفاده از API (همراه با کش)"""
        league_id = self.league_ids.get(league_key)
        if not league_id:
            return {
                'success': False,
                'error': f'لیگ {league_key} پشتیبانی نمی‌شود'
            }

        # استفاده از کش 12 ساعته
        cached = self.team_cache.get(league_key)
        if cached:
            fetched_at: datetime = cached['fetched_at']
            if (datetime.now() - fetched_at).total_seconds() <= 12 * 3600:
                return {
                    'success': True,
                    'teams': cached['teams'],
                    'cached': True
                }

        if not self.api_keys:
            return {
                'success': False,
                'error': 'هیچ کلید API برای دریافت تیم‌ها موجود نیست'
            }

        seasons_meta = await self._get_league_season_metadata(league_id)
        seasons_to_try: List[int] = []
        for season in seasons_meta:
            coverage = season.get('coverage', {}) or {}
            coverage_valid = bool(coverage.get('standings') or coverage.get('teams'))
            season_year = season.get('year')
            if coverage_valid and isinstance(season_year, int):
                seasons_to_try.append(season_year)

        if not seasons_to_try:
            seasons_to_try = [self.current_season]
            previous_season = self.current_season - 1
            if previous_season >= 2015 and previous_season not in seasons_to_try:
                seasons_to_try.append(previous_season)

        # تلاش با کلیدهای مختلف و فصل‌های متفاوت
        for api_index in range(len(self.api_keys)):
            if self.api_limits[api_index]['exhausted']:
                continue

            current_key = self.api_keys[api_index]
            self.current_api_index = api_index
            self.football_api_key = current_key

            headers = {
                'x-rapidapi-key': current_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }

            for season in seasons_to_try:
                params = {
                    'league': league_id,
                    'season': season
                }

                try:
                    response = requests.get(
                        f"{self.football_api_base}/teams",
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )

                    if not self.handle_api_response(response):
                        self.api_limits[self.current_api_index]['exhausted'] = True
                        break

                    if response.status_code == 200:
                        data = response.json()

                        errors = data.get('errors') or {}
                        if errors.get('plan'):
                            logger.warning(f"⚠️ محدودیت پلن برای لیگ {league_key} در فصل {season}: {errors.get('plan')}")
                            continue

                        teams_raw = data.get('response', [])

                        teams = []
                        for entry in teams_raw:
                            team_info = entry.get('team') or {}
                            team_id = team_info.get('id')
                            name = team_info.get('name')
                            if not team_id or not name:
                                continue
                            teams.append({
                                'team_id': team_id,
                                'team_name': name
                            })

                        if teams:
                            teams.sort(key=lambda t: t['team_name'])

                            self.team_cache[league_key] = {
                                'teams': teams,
                                'fetched_at': datetime.now(),
                                'season': season
                            }

                            logger.info(f"✅ {len(teams)} تیم برای لیگ {league_key} و فصل {season} دریافت شد")
                            return {
                                'success': True,
                                'teams': teams,
                                'season': season,
                                'cached': False
                            }
                        else:
                            logger.warning(f"⚠️ تیمی برای لیگ {league_key} در فصل {season} یافت نشد")
                    else:
                        logger.warning(f"❌ خطا در دریافت تیم‌های لیگ {league_key} (کد {response.status_code})")

                except Exception as e:
                    logger.error(f"❌ استثنا در دریافت تیم‌های لیگ {league_key}: {e}")
                    continue

        return {
            'success': False,
            'error': 'امکان دریافت لیست تیم‌ها وجود ندارد. لطفاً بعداً امتحان کنید.'
        }

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
    
    async def get_all_weekly_fixtures(self, base_date: Optional[datetime] = None) -> Dict[str, Any]:
        """دریافت برنامه بازی‌های هفتگی همه لیگ‌های مهم"""
        try:
            logger.info("🔄 درخواست فیکسچرهای هفتگی همه لیگ‌ها...")

            # محاسبه تاریخ شروع و پایان هفته
            today = base_date or datetime.now()
            days_since_saturday = (today.weekday() + 2) % 7
            saturday = today - timedelta(days=days_since_saturday)
            friday = saturday + timedelta(days=6)
            
            date_from = saturday.strftime('%Y-%m-%d')
            date_to = friday.strftime('%Y-%m-%d')
            
            # 1) تلاش برای خواندن از کش دیتابیس
            try:
                if self.db and hasattr(self.db, 'get_weekly_fixtures_cache'):
                    cached = self.db.get_weekly_fixtures_cache(saturday.date(), friday.date())
                    if cached and cached.get('payload'):
                        payload = cached['payload']
                        # اطمینان از کلیدهای پایه در payload
                        leagues = payload.get('leagues', {})
                        total_matches = payload.get('total_matches', sum(d.get('count', 0) for d in leagues.values()))
                        period = payload.get('period', f'{date_from} تا {date_to}')
                        return {
                            'success': True,
                            'leagues': leagues,
                            'total_matches': total_matches,
                            'period': period,
                            'source': 'db'
                        }
            except Exception as e:
                logger.warning(f"⚠️ خطا در خواندن کش دیتابیس: {e}")
            
            # 2) در صورت نبود کش، فراخوانی API
            current_key = self.get_current_api_key()
            if not current_key:
                return {
                    'success': False,
                    'error': 'هیچ کلید API در دسترس نیست',
                    'leagues': {},
                    'info': self.get_rate_limit_message()
                }
            
            # تلاش با کلیدهای مختلف در صورت خطا
            for api_index in range(len(self.api_keys)):
                if self.api_limits[api_index]['exhausted']:
                    continue
                    
                current_key = self.api_keys[api_index]
                self.current_api_index = api_index
                self.football_api_key = current_key
                
                headers = {
                    'x-rapidapi-key': current_key,
                    'x-rapidapi-host': 'v3.football.api-sports.io'
                }
                
                logger.info(f"🔄 استفاده از API Key {api_index}")
                
                # تلاش برای دریافت داده‌ها
                try:
                    result = await self._fetch_all_fixtures_data(saturday, friday, headers)
                    if result:
                        # ذخیره در کش دیتابیس
                        try:
                            if self.db and hasattr(self.db, 'upsert_weekly_fixtures_cache'):
                                payload = {
                                    'leagues': result.get('leagues', {}),
                                    'total_matches': result.get('total_matches', 0),
                                    'period': result.get('period', f'{date_from} تا {date_to}')
                                }
                                self.db.upsert_weekly_fixtures_cache(saturday.date(), friday.date(), payload)
                        except Exception as ce:
                            logger.warning(f"⚠️ خطا در ذخیره کش دیتابیس: {ce}")
                        # برگرداندن با منبع API
                        result['source'] = 'api'
                        return result
                except Exception as e:
                    logger.warning(f"API Key {api_index} خطا داد: {e}")
                    continue
            
            # اگر به اینجا رسیدیم، همه کلیدها خراب بودن
            return {
                'success': False,
                'error': 'تمام کلیدهای API در دسترس نیستند',
                'leagues': {},
                'info': self.get_rate_limit_message()
            }
        
        except Exception as e:
            logger.error(f"❌ خطا در get_all_weekly_fixtures: {e}")
            return {
                'success': False,
                'error': str(e),
                'leagues': {}
            }
    
    async def _fetch_all_fixtures_data(self, saturday, friday, headers):
        """دریافت داده‌های فیکسچر با هدر مشخص"""
        try:
            # لیگ‌های مهم به ترتیب اولویت
            important_leagues = [
                ('iran', 290, '🇮🇷 لیگ برتر ایران'),
                ('la_liga', 140, '🇪🇸 لالیگا (اسپانیا)'),
                ('premier_league', 39, '🏴󠁧󠁢󠁥󠁮󠁧󠁿 لیگ برتر (انگلیس)'),
                ('serie_a', 135, '🇮🇹 سری آ (ایتالیا)'),
                ('bundesliga', 78, '🇩🇪 بوندسلیگا (آلمان)'),
                ('ligue_1', 61, '🇫🇷 لیگ یک (فرانسه)'),
            ]
            
            # دریافت بازی‌ها برای هر روز
            all_day_matches = {}
            current_date = saturday
            
            while current_date <= friday:
                date_str = current_date.strftime('%Y-%m-%d')
                
                try:
                    response = requests.get(
                        f"{self.football_api_base}/fixtures",
                        headers=headers,
                        params={'date': date_str},
                        timeout=self.timeout
                    )
                    
                    # بررسی پاسخ و محدودیت
                    if not self.handle_api_response(response):
                        # اگر به محدودیت خورد، این کلید رو غیرفعال کن و None برگردون
                        self.api_limits[self.current_api_index]['exhausted'] = True
                        return None
                    
                    if response.status_code == 200:
                        data = response.json()
                        all_day_matches[date_str] = data.get('response', [])
                    else:
                        logger.warning(f"خطای API برای {date_str}: {response.status_code}")
                        all_day_matches[date_str] = []
                        
                except Exception as e:
                    logger.warning(f"خطا در دریافت بازی‌های {date_str}: {e}")
                    all_day_matches[date_str] = []
                
                current_date += timedelta(days=1)
            
            # سازماندهی بازی‌ها به تفکیک لیگ
            leagues_data = {}
            
            for league_key, league_id, league_name in important_leagues:
                league_matches = []
                
                for date_str, day_matches in all_day_matches.items():
                    for match in day_matches:
                        if match['league']['id'] == league_id:
                            fixture = match['fixture']
                            teams = match['teams']
                            goals = match['goals']
                            
                            # تبدیل به datetime برای روز هفته
                            match_date = datetime.fromisoformat(fixture['date'].replace('Z', '+00:00'))
                            
                            match_info = {
                                'fixture_id': fixture['id'],
                                'league_id': match['league']['id'],
                                'league_name': match['league']['name'],
                                'home_team_id': teams['home']['id'],
                                'home_team': teams['home']['name'],
                                'away_team_id': teams['away']['id'],
                                'away_team': teams['away']['name'],
                                'date': fixture['date'],
                                'datetime': match_date,
                                'status': fixture['status']['short'],
                                'venue': fixture['venue']['name'] if fixture.get('venue') else 'نامشخص',
                                'score': {
                                    'home': goals['home'],
                                    'away': goals['away']
                                } if goals['home'] is not None else None
                            }
                            league_matches.append(match_info)
                
                if league_matches:
                    # مرتب کردن بر اساس تاریخ
                    league_matches.sort(key=lambda x: x['datetime'])
                    leagues_data[league_key] = {
                        'name': league_name,
                        'matches': league_matches,
                        'count': len(league_matches)
                    }
            
            total_matches = sum(data['count'] for data in leagues_data.values())
            
            date_from = saturday.strftime('%Y-%m-%d')
            date_to = friday.strftime('%Y-%m-%d')
            
            logger.info(f"✅ {total_matches} بازی از {len(leagues_data)} لیگ دریافت شد")
            return {
                'success': True,
                'leagues': leagues_data,
                'total_matches': total_matches,
                'period': f'{date_from} تا {date_to}'
            }
        
        except Exception as e:
            logger.error(f"❌ خطا در _fetch_all_fixtures_data: {e}")
            return None
    
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
            
            # API-Football فقط با date کار می‌کنه نه from/to
            # باید هر روز رو جداگونه چک کنیم
            headers = {
                'x-rapidapi-key': self.football_api_key,
                'x-rapidapi-host': 'v3.football.api-sports.io'
            }
            
            all_matches = []
            
            # چک کردن هر روز از شنبه تا جمعه
            current_date = saturday
            while current_date <= friday:
                date_str = current_date.strftime('%Y-%m-%d')
                
                url = f"{self.football_api_base}/fixtures"
                params = {'date': date_str}
                
                try:
                    response = requests.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        day_matches = data.get('response', [])
                        
                        # فیلتر برای این لیگ خاص
                        for match in day_matches:
                            if match['league']['id'] == league_id:
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
                                all_matches.append(match_info)
                except Exception as e:
                    logger.warning(f"خطا در دریافت بازی‌های {date_str}: {e}")
                
                current_date += timedelta(days=1)
            
            matches = all_matches
            
            logger.info(f"✅ {len(matches)} بازی دریافت شد")
            return {
                'success': True,
                'matches': matches,
                'count': len(matches),
                'league': league,
                'period': f'{date_from} تا {date_to}'
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
            
            # بررسی آیا کلید API در دسترس هست
            current_key = self.get_current_api_key()
            if not current_key:
                return {
                    'success': False,
                    'error': 'هیچ کلید API در دسترس نیست',
                    'live_matches': [],
                    'info': self.get_rate_limit_message()
                }
            
            url = f"{self.football_api_base}/fixtures"
            params = {'live': 'all'}  # همه بازی‌های زنده
            
            # تلاش با کلیدهای مختلف در صورت خطا
            for api_index in range(len(self.api_keys)):
                if self.api_limits[api_index]['exhausted']:
                    continue
                    
                current_key = self.api_keys[api_index]
                self.current_api_index = api_index
                self.football_api_key = current_key

                headers = {
                    'x-rapidapi-key': current_key,
                    'x-rapidapi-host': 'v3.football.api-sports.io'
                }
                
                logger.info(f"🔄 استفاده از API Key {api_index} برای بازی‌های زنده")
                
                try:
                    response = requests.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=self.timeout
                    )
                    
                    # بررسی پاسخ و محدودیت
                    if not self.handle_api_response(response):
                        # اگر به محدودیت خورد، کلید رو غیرفعال کن و کلید بعدی رو امتحان کن
                        self.api_limits[api_index]['exhausted'] = True
                        continue
                    
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
                                'competition': league.get('name') or league.get('round') or 'نامشخص',
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
                        continue  # امتحان کلید بعدی
                    
                except Exception as e:
                    logger.warning(f"API Key {api_index} خطا داد: {e}")
                    continue  # امتحان کلید بعدی
            
            # اگر به اینجا رسیدیم، همه کلیدها خراب بودن
            return {
                'success': False,
                'error': 'تمام کلیدهای API در دسترس نیستند',
                'live_matches': [],
                'info': self.get_rate_limit_message()
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
    
    def format_all_fixtures_message(self, all_fixtures_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام برنامه بازی‌های همه لیگ‌ها"""
        if not all_fixtures_data.get('success'):
            error = all_fixtures_data.get('error', 'خطای ناشناخته')
            message = f"❌ خطا در دریافت برنامه بازی‌ها:\n{error}"
            if all_fixtures_data.get('info'):
                message += f"\n\n💡 {all_fixtures_data['info']}"
            return message
        
        leagues_data = all_fixtures_data.get('leagues', {})
        if not leagues_data:
            return "❌ هیچ بازی‌ای در این هفته یافت نشد"
        
        # نقشه روزهای هفته به فارسی
        weekday_fa = {
            0: 'دوشنبه',
            1: 'سه‌شنبه',
            2: 'چهارشنبه',
            3: 'پنج‌شنبه',
            4: 'جمعه',
            5: 'شنبه',
            6: 'یک‌شنبه'
        }
        
        message = f"⚽ **برنامه بازی‌های هفتگی**\n"
        message += f"📅 {all_fixtures_data.get('period', '')}\n"
        message += f"🎯 جمع: {all_fixtures_data.get('total_matches', 0)} بازی\n"
        message += "\n" + "=" * 40 + "\n\n"
        
        # نمایش به ترتیب اولویت (ایران اول)
        league_order = ['iran', 'la_liga', 'premier_league', 'serie_a', 'bundesliga', 'ligue_1']
        
        for league_key in league_order:
            if league_key not in leagues_data:
                continue
            
            league_info = leagues_data[league_key]
            message += f"{league_info['name']}\n"
            message += f"🎯 {league_info['count']} بازی\n\n"
            
            for match in league_info['matches']:
                # تبدیل به تایم‌زون تهران
                match_dt_utc = match['datetime']
                tehran_tz = pytz.timezone('Asia/Tehran')
                match_dt = match_dt_utc.astimezone(tehran_tz)
                
                weekday = weekday_fa[match_dt.weekday()]
                date_str = match_dt.strftime('%m/%d')
                time_str = match_dt.strftime('%H:%M')
                
                # نمایش بازی
                if match.get('score'):
                    # بازی انجام شده
                    score_h = match['score']['home']
                    score_a = match['score']['away']
                    message += f"🟢 {match['home_team']} {score_h}-{score_a} {match['away_team']}\n"
                    message += f"   📅 {weekday} {date_str} - ✅ تمام شده\n"
                else:
                    # بازی آینده
                    message += f"⚪ {match['home_team']} vs {match['away_team']}\n"
                    message += f"   📅 {weekday} {date_str} - ⏰ {time_str}\n"
                
                message += "\n"
            
            message += "=" * 40 + "\n\n"
        
        source = all_fixtures_data.get('source', 'api')
        source_text = "از دیتابیس" if source == 'db' else "از API"
        message += "📊 منبع: API-Football\n"
        message += f"🗂️ داده: {source_text}"
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

    def _hydrate_match_datetime(self, fixture):
        """تبدیل تاریخ بازی به شیء datetime با پشتیبانی از کلیدهای مختلف"""
        raw_dt = (
            fixture.get('match_datetime')
            or fixture.get('datetime')
            or fixture.get('date')
        )

        if not raw_dt:
            return None

        if isinstance(raw_dt, datetime):
            return raw_dt

        if isinstance(raw_dt, dict) and raw_dt.get('iso'):
            raw_dt = raw_dt['iso']

        if isinstance(raw_dt, str):
            normalized = raw_dt.replace('Z', '+00:00').strip()
            try:
                return datetime.fromisoformat(normalized)
            except ValueError:
                try:
                    return parser.isoparse(normalized)
                except (ValueError, TypeError):
                    logger.warning(f"⚠️ فرمت تاریخ ناشناخته برای فیکسچر: {raw_dt}")
                    return None

        logger.warning(f"⚠️ فرمت تاریخ پشتیبانی‌نشده برای فیکسچر: {type(raw_dt)}")
        return None

    def format_all_fixtures_message(self, all_fixtures_data: Dict[str, Any]) -> str:
        """فرمت کردن پیام برنامه بازی‌های همه لیگ‌ها"""
        if not all_fixtures_data.get('success'):
            error = all_fixtures_data.get('error', 'خطای ناشناخته')
            message = f"❌ خطا در دریافت برنامه بازی‌ها:\n{error}"
            if all_fixtures_data.get('info'):
                message += f"\n\n💡 {all_fixtures_data['info']}"
            return message
        
        leagues_data = all_fixtures_data.get('leagues', {})
        if not leagues_data:
            return "❌ هیچ بازی‌ای در این هفته یافت نشد"
        
        # نقشه روزهای هفته به فارسی
        weekday_fa = {
            0: 'دوشنبه',
            1: 'سه‌شنبه',
            2: 'چهارشنبه',
            3: 'پنج‌شنبه',
            4: 'جمعه',
            5: 'شنبه',
            6: 'یک‌شنبه'
        }
        
        message = f"⚽ **برنامه بازی‌های هفتگی**\n"
        message += f"📅 {all_fixtures_data.get('period', '')}\n"
        message += f"🎯 جمع: {all_fixtures_data.get('total_matches', 0)} بازی\n"
        message += "\n" + "=" * 40 + "\n\n"
        
        # نمایش به ترتیب اولویت (ایران اول)
        league_order = ['iran', 'la_liga', 'premier_league', 'serie_a', 'bundesliga', 'ligue_1']
        
        for league_key in league_order:
            if league_key not in leagues_data:
                continue
            
            league_info = leagues_data[league_key]
            message += f"{league_info['name']}\n"
            message += f"🎯 {league_info['count']} بازی\n\n"
            
            for match in league_info['matches']:
                match_dt_utc = self._hydrate_match_datetime(match)
                if not match_dt_utc:
                    message += f"⚪ {match['home_team']} vs {match['away_team']}\n"
                    message += "   📅 زمان نامشخص\n\n"
                    continue
                match['match_datetime'] = match_dt_utc
                # تبدیل به تایم‌زون تهران
                tehran_tz = pytz.timezone('Asia/Tehran')
                match_dt = match_dt_utc.astimezone(tehran_tz)
                
                weekday = weekday_fa[match_dt.weekday()]
                date_str = match_dt.strftime('%m/%d')
                time_str = match_dt.strftime('%H:%M')
                
                # نمایش بازی
                if match.get('score'):
                    # بازی انجام شده
                    score_h = match['score']['home']
                    score_a = match['score']['away']
                    message += f"🟢 {match['home_team']} {score_h}-{score_a} {match['away_team']}\n"
                    message += f"   📅 {weekday} {date_str} - ✅ تمام شده\n"
                else:
                    # بازی آینده
                    message += f"⚪ {match['home_team']} vs {match['away_team']}\n"
                    message += f"   📅 {weekday} {date_str} - ⏰ {time_str}\n"
                
                message += "\n"
            
            message += "=" * 40 + "\n\n"
        
        source = all_fixtures_data.get('source', 'api')
        source_text = "از دیتابیس" if source == 'db' else "از API"
        message += "📊 منبع: API-Football\n"
        message += f"🗂️ داده: {source_text}"
        return message
