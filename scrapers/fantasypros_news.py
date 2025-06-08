import requests
from bs4 import BeautifulSoup

def scrape_fantasypros_news(max_items=10):
    """
    Scrapes the latest NFL news headlines from FantasyPros.
    Returns a list of dicts: {headline, summary, time}
    """
    url = "https://www.fantasypros.com/nfl/news.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    news_items = []
    for article in soup.select('div.news-feed-item'):
        headline_tag = article.find('a', class_='news-feed-title')
        summary_tag = article.find('div', class_='news-feed-summary')
        time_tag = article.find('span', class_='news-feed-date')
        url = headline_tag['href'] if headline_tag and headline_tag.has_attr('href') else ''
        if url and url.startswith('/'):
            url = f'https://www.fantasypros.com{url}'
        if not headline_tag:
            continue
        headline = headline_tag.get_text(strip=True)
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        time_str = time_tag.get_text(strip=True) if time_tag else ''
        news_items.append({
            'headline': headline,
            'summary': summary,
            'time': time_str,
            'url': url
        })
        if len(news_items) >= max_items:
            break
    return news_items
