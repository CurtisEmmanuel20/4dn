def load_fake_injury_data(player):
    return [
        {"date": "2024-10-10", "type": "Ankle Sprain", "weeks_out": 4, "status": "Questionable"},
        {"date": "2023-12-02", "type": "Hamstring", "weeks_out": 2, "status": "Recovered"},
    ]

def load_fake_news(player):
    return [
        {"title": "Player returns to limited practice", "source": "ESPN", "link": "#"},
        {"title": "Team cautious with injury recovery", "source": "NFL.com", "link": "#"}
    ]

def load_fake_tweets(player):
    return [
        {"handle": "@AdamSchefter", "text": f"{player} expected to be out 2–4 weeks, per source."},
        {"handle": "@FantasyPtsMed", "text": f"{player} is trending toward a Week 3 return."}
    ]

def generate_ai_summary(player, injuries, news, tweets):
    if not injuries:
        return f"No significant injury data found for {player}."
    latest = injuries[0]
    injury_type = latest['type']
    weeks_out = latest['weeks_out']
    return (
        f"It appears that {player} has suffered a {injury_type.lower()}, typically requiring "
        f"{weeks_out}-week recovery. This assessment is based on reports from ESPN, Yahoo, and analysts like "
        f"Adam Schefter on X."
    )
