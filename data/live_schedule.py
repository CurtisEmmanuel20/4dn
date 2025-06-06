"""
Fetches and returns live NFL schedule data from ESPN.
Standardizes output to match the schema used by the previous fake data functions.
"""
import requests
import json
import os
from config import ESPN_SCHEDULE_API_URL, SCHEDULE_CACHE, SCRAPING_START_DATE
from datetime import datetime

def get_live_schedule():
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        return []
    try:
        resp = requests.get(ESPN_SCHEDULE_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Parse ESPN API JSON to standardized format
        schedule = []
        events = data.get('events', [])
        for event in events:
            competitions = event.get('competitions', [])
            if not competitions:
                continue
            comp = competitions[0]
            home_team = None
            away_team = None
            for team in comp.get('competitors', []):
                if team.get('homeAway') == 'home':
                    home_team = team.get('team', {}).get('displayName')
                elif team.get('homeAway') == 'away':
                    away_team = team.get('team', {}).get('displayName')
            date_str = event.get('date', '')  # ISO format
            # Convert to YYYY-MM-DD and HH:MM (local time)
            from dateutil import parser, tz
            try:
                dt = parser.isoparse(date_str).astimezone(tz.gettz('US/Eastern'))
                date = dt.strftime('%Y-%m-%d')
                time = dt.strftime('%H:%M')
            except Exception:
                date = date_str[:10]
                time = date_str[11:16] if len(date_str) > 15 else ''
            schedule.append({
                'home_team': home_team,
                'away_team': away_team,
                'date': date,
                'time': time
            })
        # Save to cache
        with open(SCHEDULE_CACHE, 'w') as f:
            json.dump(schedule, f)
        return schedule
    except Exception as e:
        # Fallback to cache
        if os.path.exists(SCHEDULE_CACHE):
            with open(SCHEDULE_CACHE, 'r') as f:
                return json.load(f)
        return []
