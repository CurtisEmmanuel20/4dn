# config.py
"""
Central configuration for all data source URLs, API keys, and endpoints.
"""

import os
from datetime import datetime

# FantasyPros (for player stats and projections)
FANTASYPROS_BASE_URL = "https://www.fantasypros.com/nfl/projections/"
FANTASYPROS_PLAYER_PROJECTIONS_URL = FANTASYPROS_BASE_URL  # Alias for compatibility
PLAYER_CACHE = os.path.join(os.path.dirname(__file__), "data", "player_cache.json")
FANTASYPROS_API_KEY = os.getenv("FANTASYPROS_API_KEY", "")  # If needed

# Yahoo (for news and injuries)
YAHOO_NEWS_API_URL = "https://sports.yahoo.com/nfl/players/"
YAHOO_API_KEY = os.getenv("YAHOO_API_KEY", "")

# ESPN (for schedules)
ESPN_SCHEDULE_API_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
ESPN_API_KEY = os.getenv("ESPN_API_KEY", "")

# Twitter/X (for social injury news)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# WeatherAPI (for weather data)
WEATHERAPI_KEY = "de6402faa35a1dd3e63d967693485e3e"

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

# Data refresh intervals (in seconds)
PLAYER_STATS_REFRESH_INTERVAL = 24 * 60 * 60  # 24 hours
INJURY_REFRESH_INTERVAL = 4 * 60 * 60        # 4 hours
SCHEDULE_REFRESH_INTERVAL = 24 * 60 * 60     # 24 hours

# 📅 Set scraping start date
SCRAPING_START_DATE = datetime(2025, 7, 16)

# Add any other global config here
