import requests
from bs4 import BeautifulSoup
import re

def scrape_espn_news(max_items=10):
    """
    Scrapes the latest NFL news headlines from ESPN.
    Returns a list of dicts: {headline, summary, time, url}
    """
    url = "https://www.espn.com/nfl/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []
    # Find all top headlines links
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Only grab main NFL news stories
        if re.match(r"https://www.espn.com/nfl/story/.*", href):
            headline = a.get_text(strip=True)
            if not headline or len(headline) < 8:
                continue
            news_items.append({
                'headline': headline,
                'summary': '',
                'time': '',
                'url': href
            })
            if len(news_items) >= max_items:
                break
    return news_items
