from datetime import datetime, timedelta
from schedule_scraper import fetch_yahoo_schedule
from utils import cache
from config import WEATHERAPI_KEY, SCRAPING_START_DATE
import requests
import json

def get_weather_forecast(city, date):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_KEY}&q={city}&dt={date}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            forecast = data.get("forecast", {}).get("forecastday", [{}])[0]
            day = forecast.get("day", {})
            return {
                "temp": day.get("avgtemp_f"),
                "rain_chance": day.get("daily_chance_of_rain"),
                "wind_mph": day.get("maxwind_mph"),
                "condition": day.get("condition", {}).get("text", "")
            }
        else:
            return {"error": f"WeatherAPI error {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def recheck_weather_for_games():
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        return
    
    today = datetime.now().date()
    schedule = fetch_yahoo_schedule()
    with open("nfl_stadiums.json", "r") as f:
        stadium_map = json.load(f)
    for game in schedule:
        # Parse date to YYYY-MM-DD
        date_str = game.get('date', '')
        try:
            from dateutil import parser
            game_date = parser.parse(date_str + f" {today.year}").date()
        except Exception:
            continue
        days_until = (game_date - today).days
        if days_until not in [7, 3, 1]:
            continue
        if game.get("is_dome", False):
            continue
        # Find city
        city = None
        stadium = game.get('stadium', '').strip()
        for team, mapped_city in stadium_map.items():
            if stadium and stadium.lower() in team.lower():
                city = mapped_city
                break
        if not city:
            home_team = game.get('team_home', '')
            for team, mapped_city in stadium_map.items():
                if home_team.lower() in team.lower():
                    city = mapped_city
                    break
        if not city:
            continue
        date_api = game_date.strftime('%Y-%m-%d')
        weather = get_weather_forecast(city, date_api)
        cache.cache_data(f"weather_{game['game_id']}_{date_api}", weather, ttl=12*60*60)
