import requests
import json
import os
from datetime import datetime
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

API_KEY = "de6402faa35a1dd3e63d967693485e3e"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"
CACHE_FILE = "cached_weather.json"

with open("nfl_stadiums.json", "r") as f:
    stadium_map = json.load(f)

def get_cached_weather():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def save_cached_weather(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def get_game_weather(team_name, date):
    cache = get_cached_weather()
    if team_name in cache and date in cache[team_name]:
        return cache[team_name][date]

    city = stadium_map.get(team_name)
    if not city:
        return {"error": "Unknown team"}

    params = {"q": city, "appid": API_KEY, "units": "imperial"}
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    forecast = [
        {
            "time": entry["dt_txt"],
            "temp": entry["main"]["temp"],
            "wind": entry["wind"]["speed"],
            "weather": entry["weather"][0]["description"]
        }
        for entry in data.get("list", []) if date in entry["dt_txt"]
    ]

    if team_name not in cache:
        cache[team_name] = {}
    cache[team_name][date] = forecast
    save_cached_weather(cache)

    return forecast

def refresh_all_weather():
    today = datetime.now(timezone("US/Eastern")).strftime("%Y-%m-%d")
    for team, city in stadium_map.items():
        get_game_weather(team, today)

def schedule_weather_refresh():
    scheduler = BackgroundScheduler(timezone="US/Eastern")
    scheduler.add_job(refresh_all_weather, 'cron', hour=0, minute=0)
    scheduler.start()
