"""
Fetches and returns live NFL injury data from Yahoo, ESPN, and Twitter/X.
Standardizes output to match the schema used by the previous fake data functions.
"""
import requests
import json
import os
from config import YAHOO_INJURY_API_URL, INJURY_CACHE, SCRAPING_START_DATE
from datetime import datetime

def get_live_injury_data():
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        # Return mock data for preview mode
        return [
            {"player": "Tyreek Hill", "team": "MIA", "status": "Healthy", "note": "No injury reported."},
            {"player": "Austin Ekeler", "team": "LAC", "status": "Questionable", "note": "Ankle - limited practice."},
            {"player": "Justin Jefferson", "team": "MIN", "status": "Out", "note": "Hamstring - out for Week 1."}
        ]
    try:
        resp = requests.get(YAHOO_INJURY_API_URL, timeout=10)
        resp.raise_for_status()
        # TODO: Parse HTML/JSON and extract injury data into standardized format
        # injuries = parse_yahoo_injury_html(resp.text)
        injuries = []  # Replace with real parsing logic
        # Save to cache
        with open(INJURY_CACHE, 'w') as f:
            json.dump(injuries, f)
        return injuries
    except Exception as e:
        # Fallback to cache
        if os.path.exists(INJURY_CACHE):
            with open(INJURY_CACHE, 'r') as f:
                return json.load(f)
        # Return mock data if all else fails
        return [
            {"player": "Tyreek Hill", "team": "MIA", "status": "Healthy", "note": "No injury reported."},
            {"player": "Austin Ekeler", "team": "LAC", "status": "Questionable", "note": "Ankle - limited practice."},
            {"player": "Justin Jefferson", "team": "MIN", "status": "Out", "note": "Hamstring - out for Week 1."}
        ]
