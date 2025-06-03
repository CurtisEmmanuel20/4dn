import random
from datetime import datetime
# from utils import calculate_confidence_score  # Uncomment if you add this util

PLAYER_POOL = [
    {
        "name": "Raheem Mostert",
        "team": "MIA",
        "position": "RB",
        "matchup": "vs CAR",
        "def_rank": 31,
        "opp_injuries": ["LB Frankie Luvu – Out"],
        "status": "Healthy",
        "snap_trend": [71, 74, 72],
        "red_zone_looks": 3,
        "weather": "Clear 75°F",
        "similar_games": [{"vs": "NYG", "points": 19.2}, {"vs": "HOU", "points": 20.8}],
        "ai_blurb": "Soft matchup and elite red zone usage.",
    },
    # Add 20+ more with varied data
    {
        "name": "CeeDee Lamb",
        "team": "DAL",
        "position": "WR",
        "matchup": "@ WAS",
        "def_rank": 29,
        "opp_injuries": ["CB Kendall Fuller – Questionable"],
        "status": "Healthy",
        "snap_trend": [92, 91, 93],
        "red_zone_looks": 2,
        "weather": "Dome",
        "similar_games": [{"vs": "NYG", "points": 24.1}, {"vs": "PHI", "points": 18.7}],
        "ai_blurb": "Elite WR1 usage and soft secondary.",
    },
    {
        "name": "Jared Goff",
        "team": "DET",
        "position": "QB",
        "matchup": "vs CHI",
        "def_rank": 28,
        "opp_injuries": ["S Eddie Jackson – Out"],
        "status": "Healthy",
        "snap_trend": [100, 100, 100],
        "red_zone_looks": 0,
        "weather": "Dome",
        "similar_games": [{"vs": "GB", "points": 22.3}, {"vs": "MIN", "points": 19.5}],
        "ai_blurb": "High floor, high ceiling spot at home.",
    },
    {
        "name": "Bijan Robinson",
        "team": "ATL",
        "position": "RB",
        "matchup": "@ ARI",
        "def_rank": 32,
        "opp_injuries": ["LB Kyzir White – Out"],
        "status": "Healthy",
        "snap_trend": [68, 70, 72],
        "red_zone_looks": 4,
        "weather": "Dome",
        "similar_games": [{"vs": "TB", "points": 17.8}, {"vs": "NO", "points": 21.2}],
        "ai_blurb": "Facing league-worst run D, heavy RZ work.",
    },
    {
        "name": "Mike Evans",
        "team": "TB",
        "position": "WR",
        "matchup": "vs IND",
        "def_rank": 30,
        "opp_injuries": ["CB Kenny Moore – Out"],
        "status": "Healthy",
        "snap_trend": [89, 87, 90],
        "red_zone_looks": 3,
        "weather": "Clear 78°F",
        "similar_games": [{"vs": "CAR", "points": 23.0}, {"vs": "ATL", "points": 19.4}],
        "ai_blurb": "Red zone monster, plus matchup for deep shots.",
    },
    {
        "name": "David Njoku",
        "team": "CLE",
        "position": "TE",
        "matchup": "@ DEN",
        "def_rank": 27,
        "opp_injuries": ["LB Josey Jewell – Out"],
        "status": "Healthy",
        "snap_trend": [85, 83, 86],
        "red_zone_looks": 2,
        "weather": "Clear 60°F",
        "similar_games": [{"vs": "BAL", "points": 15.2}, {"vs": "PIT", "points": 13.7}],
        "ai_blurb": "Consistent usage, defense weak vs TEs.",
    },
    {
        "name": "James Cook",
        "team": "BUF",
        "position": "RB",
        "matchup": "@ LV",
        "def_rank": 26,
        "opp_injuries": ["DT Jerry Tillery – Out"],
        "status": "Healthy",
        "snap_trend": [62, 65, 67],
        "red_zone_looks": 2,
        "weather": "Dome",
        "similar_games": [{"vs": "NYJ", "points": 16.4}, {"vs": "MIA", "points": 18.1}],
        "ai_blurb": "Explosive back, faces bottom-5 run D.",
    },
    # ...add more for realism
]

current_elite_players = []

def is_trending_down(player):
    return (
        player["snap_trend"][-1] < player["snap_trend"][-2] - 5
        or player["def_rank"] < 15
        or "Questionable" in player["status"] or "Out" in player["status"]
    )

def refresh_elite_matchups():
    global current_elite_players
    preserved = [p for p in current_elite_players if not is_trending_down(p)]
    needed = 7 - len(preserved)
    available_candidates = [p for p in PLAYER_POOL if p not in preserved]
    replacements = random.sample(available_candidates, needed) if needed > 0 and len(available_candidates) >= needed else []
    current_elite_players = preserved + replacements
    return current_elite_players
