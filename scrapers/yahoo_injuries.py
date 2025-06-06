import requests
from bs4 import BeautifulSoup
from config import SCRAPING_START_DATE
from datetime import datetime

def scrape_yahoo_injuries():
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        return []

    url = "https://sports.yahoo.com/nfl/injuries/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    injury_data = []

    tables = soup.find_all("table")
    for table in tables:
        team_header = table.find_previous("h3")
        team_name = team_header.text.strip() if team_header else "Unknown"

        for row in table.find("tbody").find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 5:
                continue
            injury_data.append({
                "player": cols[0].text.strip(),
                "position": cols[1].text.strip(),
                "injury": cols[2].text.strip(),
                "status": cols[3].text.strip(),
                "updated": cols[4].text.strip(),
                "team": team_name,
            })

    return injury_data
