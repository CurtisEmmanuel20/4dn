def calculate_4dn_score(player):
    weights = {
        "yahoo_rank_score": 0.10,
        "fantasypros_rank_score": 0.10,
        "matchup_difficulty_score": 0.15,
        "injury_risk_score": 0.15,
        "weather_score": 0.05,
        "snap_trend_score": 0.20,
        "usage_score": 0.20,
        "recent_performance_score": 0.05
    }
    defaults = {
        "yahoo_rank_score": 50,
        "fantasypros_rank_score": 50,
        "matchup_difficulty_score": 50,
        "injury_risk_score": 30,
        "weather_score": 50,
        "snap_trend_score": 50,
        "usage_score": 50,
        "recent_performance_score": 50
    }
    score = 0
    for key, weight in weights.items():
        value = player.get(key)
        score += (value if value is not None else defaults[key]) * weight
    return round(score, 2)
