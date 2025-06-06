from schedule_scraper import fetch_yahoo_schedule
from utils.weather import get_weather_forecast
from datetime import datetime

def get_upcoming_game_for_team(team):
    today = datetime.today().date()
    schedule = fetch_yahoo_schedule()
    for game in schedule:
        try:
            from dateutil import parser
            game_date = parser.parse(game["date"] + f" {today.year}").date()
        except Exception:
            continue
        days_until = (game_date - today).days
        if 0 <= days_until <= 7 and team in (game["team_home"], game["team_away"]):
            game["date"] = game_date.isoformat()
            game["days_until"] = days_until
            return game
    return None

def attach_weather_data(game):
    if game.get("is_dome", False):
        game["weather"] = {"note": "No weather impact. Game is in a dome."}
        return game
    if game.get("days_until", 999) > 7:
        game["weather"] = {"note": "Too early for weather forecast (game > 7 days away)."}
        return game
    forecast = get_weather_forecast(game["stadium"], game["date"])
    game["weather"] = forecast
    return game

def calculate_matchup_score(player_team):
    game = get_upcoming_game_for_team(player_team)
    if not game:
        return {"error": "No upcoming game found."}
    game = attach_weather_data(game)
    # Example: confidence scoring logic
    score = 1.0
    weather = game.get("weather", {})
    if "note" in weather:
        confidence = 1.0
    else:
        confidence = 1.0
        if weather.get("rain_chance", 0) and int(weather["rain_chance"]) > 50:
            confidence -= 0.2
        if weather.get("wind_mph", 0) and float(weather["wind_mph"]) > 15:
            confidence -= 0.2
        if weather.get("condition", "").lower() in ["snow", "thunderstorm"]:
            confidence -= 0.3
        confidence = max(0.1, confidence)
    return {"game": game, "confidence": confidence, "matchup_score": score * confidence}
