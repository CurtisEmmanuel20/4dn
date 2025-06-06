from config import WEATHERAPI_KEY, SCRAPING_START_DATE
import requests
from datetime import datetime
import importlib.util
import os

scheduler_path = os.path.join(os.path.dirname(__file__), 'scheduler.py')
spec = importlib.util.spec_from_file_location('scheduler', scheduler_path)
scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduler)
should_use_real_data = scheduler.should_use_real_data

def get_weather_forecast(city, date):
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        return {"note": f"Scraping locked until {SCRAPING_START_DATE.strftime('%B %d, %Y')}."}
    
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

def get_game_weather_data(games):
    if should_use_real_data():
        # TO BE IMPLEMENTED: Real weather data fetching for a list of games
        return []
    else:
        # Return mock weather data for preview mode
        return [
            {"game": "MIA vs LAC", "city": "Miami", "date": "2025-09-07", "forecast": {"temp": 88, "rain_chance": 10, "wind_mph": 7, "condition": "Sunny"}},
            {"game": "KC vs BUF", "city": "Kansas City", "date": "2025-09-07", "forecast": {"temp": 81, "rain_chance": 20, "wind_mph": 12, "condition": "Partly Cloudy"}},
        ]

def get_weather_score(stadium_name, city, date, weather_data=None):
    """
    Returns a weather impact score for a game. If the game is in a dome, returns 0.0.
    Otherwise, uses weather data (live or cached) to compute the score.
    Args:
        stadium_name (str): Name of the stadium.
        city (str): City where the game is played.
        date (str): Date of the game (YYYY-MM-DD).
        weather_data (dict, optional): Pre-fetched weather data. If None, will fetch.
    Returns:
        float: Weather impact score (rounded to 1 decimal place).
    """
    DOME_STADIUMS = [
        'SoFi Stadium', 'AT&T Stadium', 'Caesars Superdome', 'Allegiant Stadium',
        'Lucas Oil Stadium', 'NRG Stadium', 'U.S. Bank Stadium', 'State Farm Stadium',
        'Ford Field', 'Mercedes-Benz Stadium', 'Syracuse Dome', 'The Dome at America’s Center',
        'Metrodome', 'Georgia Dome', 'Edward Jones Dome', 'Tropicana Field', 'Olympic Stadium',
        'Rogers Centre', 'Astrodome', 'Kingdome', 'Pontiac Silverdome', 'Hubert H. Humphrey Metrodome'
    ]
    if stadium_name in DOME_STADIUMS:
        return 0.0

    # Try to use provided weather_data, else fetch
    if weather_data is None:
        try:
            from utils.weather import get_weather_forecast
        except ImportError:
            from .weather import get_weather_forecast
        weather_data = get_weather_forecast(city, date)

    # If weather data is missing or error, return 0.0
    if not weather_data or 'error' in weather_data or 'note' in weather_data:
        return 0.0

    score = 0.0
    try:
        wind = float(weather_data.get('wind_mph', 0) or 0)
        rain = float(weather_data.get('rain_chance', 0) or 0)
        temp = float(weather_data.get('temp', 70) or 70)
        if wind > 20:
            score += 2.0
        if rain > 60:
            score += 1.5
        if temp < 35 or temp > 90:
            score += 1.0
    except Exception:
        return 0.0
    return round(score, 1)
