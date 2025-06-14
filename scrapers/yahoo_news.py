import requests
from bs4 import BeautifulSoup
import re
import os
import json

def scrape_yahoo_news(max_items=20):
    """
    Scrapes the latest NFL and general football news headlines from Yahoo Sports.
    Returns a list of dicts: {headline, summary, time, url}
    """
    url = "https://sports.yahoo.com/nfl/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    news_items = []
    seen = set()
    # Grab all news articles in the main feed
    for article in soup.find_all(['li', 'div'], class_=re.compile(r'js-stream-content')):
        headline_tag = article.find('h3')
        summary_tag = article.find('p')
        time_tag = article.find('time')
        link_tag = article.find('a', href=True)
        if not headline_tag or not link_tag:
            continue
        headline = headline_tag.get_text(strip=True)
        if headline in seen:
            continue
        seen.add(headline)
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        time_str = time_tag.get_text(strip=True) if time_tag else ''
        url = link_tag['href']
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
    # Save to disk for fallback
    if news_items:
        try:
            with open('data/yahoo_news_cache.json', 'w', encoding='utf-8') as f:
                json.dump(news_items, f)
        except Exception:
            pass
    return news_items

def get_yahoo_news_fallback(count=7):
    """
    Loads cached Yahoo news from disk for fallback.
    """
    try:
        with open('data/yahoo_news_cache.json', 'r', encoding='utf-8') as f:
            news_items = json.load(f)
        return news_items[:count]
    except Exception:
        return []
