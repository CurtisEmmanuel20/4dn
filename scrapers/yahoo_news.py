import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_yahoo_news(max_items=10):
    """
    Scrapes the latest NFL news headlines from Yahoo Sports.
    Returns a list of dicts: {headline, summary, time}
    """
    url = "https://sports.yahoo.com/nfl/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    news_items = []
    # Yahoo's NFL news headlines are typically in <li> or <div> elements with specific classes
    # We'll look for headline blocks in the main news section
    for article in soup.select('li.js-stream-content, div.js-stream-content'):
        headline_tag = article.find('h3')
        summary_tag = article.find('p')
        time_tag = article.find('time')
        link_tag = article.find('a', href=True)
        if not headline_tag:
            continue
        headline = headline_tag.get_text(strip=True)
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        time_str = time_tag.get_text(strip=True) if time_tag else ''
        url = link_tag['href'] if link_tag else ''
        # Yahoo sometimes uses relative URLs
        if url and url.startswith('/'):
            url = f'https://sports.yahoo.com{url}'
        news_items.append({
            'headline': headline,
            'summary': summary,
            'time': time_str,
            'url': url
        })
        if len(news_items) >= max_items:
            break
    return news_items
