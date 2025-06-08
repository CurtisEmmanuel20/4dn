import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

CACHE_PATH = "caching/fantasy_cache.json"

def scrape_fantasypros_rankings():
    url = "https://www.fantasypros.com/nfl/rankings/half-point-ppr-cheatsheets.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    players = []
    rows = soup.select('table tbody tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            players.append({
                "name": cols[1].get_text(strip=True),
                "team": cols[2].get_text(strip=True),
                "position": cols[3].get_text(strip=True),
                "bye_week": cols[4].get_text(strip=True)
            })
    return players

def scrape_yahoo_adp():
    url = "https://sports.yahoo.com/fantasy/article/fantasy-football-rankings-2025-144031309.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Assume structured list or block parsing; placeholder logic:
    return []

def cache_player_data(data):
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "players": data
        }, f)

def load_cached_data():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f).get("players", [])
    return []
