import requests
from bs4 import BeautifulSoup
from config import SCRAPING_START_DATE
from datetime import datetime

def scrape_yahoo_schedule():
    if datetime.now() < SCRAPING_START_DATE:
        print("⏳ Scraping is locked until", SCRAPING_START_DATE.strftime('%B %d, %Y'))
        return []

    url = "https://sports.yahoo.com/nfl/schedule/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    game_data = []

    week_blocks = soup.find_all("div", class_="Mb(20px)")
    for week in week_blocks:
        date_header = week.find("h3")
        game_date = date_header.text.strip() if date_header else "TBD"

        games = week.find_all("li", class_="Mb(10px)")
        for game in games:
            teams = game.find_all("span", class_="Fz(14px)")
            if len(teams) < 2:
                continue

            time_el = game.find("div", class_="Fz(11px)")
            time_str = time_el.text.strip() if time_el else "TBD"

            stadium = game.find("div", class_="D(ib)").text if game.find("div", class_="D(ib)") else "Unknown"
            link = game.find("a")["href"] if game.find("a") else ""

            game_data.append({
                "date": game_date,
                "time": time_str,
                "team_away": teams[0].text.strip(),
                "team_home": teams[1].text.strip(),
                "stadium": stadium,
                "game_link": f"https://sports.yahoo.com{link}" if link else "",
                "source": "Yahoo"
            })

    return game_data
