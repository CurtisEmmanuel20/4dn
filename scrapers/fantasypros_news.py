import requests
from bs4 import BeautifulSoup
import re

def scrape_fantasypros_news(max_items=10):
    """
    Scrapes the latest NFL news headlines from FantasyPros.
    Returns a list of dicts: {headline, summary, time, url}
    """
    url = "https://www.fantasypros.com/nfl/news.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []
    # Find all news links that look like player news
    for a in soup.find_all('a', href=True):
        href = a['href']
        if re.match(r"/nfl/news/\\d+/[a-z0-9\-]+.php", href):
            headline = a.get_text(strip=True)
            url_full = f'https://www.fantasypros.com{href}'
            # Try to get summary and time from nearby elements
            parent = a.find_parent('div')
            summary = ''
            time_str = ''
            if parent:
                # Look for summary in next siblings
                next_div = parent.find_next_sibling('div')
                if next_div:
                    summary = next_div.get_text(strip=True)
                # Look for time in previous siblings
                prev_div = parent.find_previous_sibling('div')
                if prev_div and 'EDT' in prev_div.get_text():
                    time_str = prev_div.get_text(strip=True)
            news_items.append({
                'headline': headline,
                'summary': summary,
                'time': time_str,
                'url': url_full
            })
            if len(news_items) >= max_items:
                break
    return news_items
