from scrapers.yahoo_schedule import scrape_yahoo_schedule
from constants import DOME_STADIUMS
from utils import cache

def fetch_yahoo_schedule():
    cached = cache.get_cached_data("yahoo_schedule")
    if cached:
        schedule = cached
    else:
        schedule = scrape_yahoo_schedule()
        cache.cache_data("yahoo_schedule", schedule, ttl=21600)  # 6 hours
    for game in schedule:
        game["is_dome"] = game.get("stadium", "") in DOME_STADIUMS
    return schedule
