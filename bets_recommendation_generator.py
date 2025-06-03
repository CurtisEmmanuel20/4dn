import json
from datetime import datetime
from random import randint, choice

def generate_bets_data():
    # Simulate a growing list of bets for demo purposes
    teams = ["Chiefs", "49ers", "Eagles", "Bills", "Jets", "Browns", "Rams", "Cowboys", "Packers", "Dolphins", "Patriots", "Giants", "Vikings", "Seahawks", "Bengals"]
    notes = [
        "Mahomes vs bottom-10 defense", "Elite defense and home advantage", "Strong home trends", "Underdog with upside", "QB mismatch", "Injury boost", "Weather edge", "Revenge game", "Division rivalry", "Hot streak"
    ]
    moneyline_picks = []
    for _ in range(randint(4, 8)):
        team = choice(teams)
        odds = f"-{randint(110, 250)}"
        confidence = randint(60, 90)
        note = choice(notes)
        moneyline_picks.append({
            "team": team,
            "odds": odds,
            "confidence": confidence,
            "note": note
        })
    parlay_recommendations = []
    for _ in range(randint(2, 4)):
        legs = [f"{choice(teams)} ML" for _ in range(randint(2, 4))]
        risk = choice(["Safe", "Moderate", "Aggressive"])
        payout = f"+{randint(150, 1200)}"
        note = choice(notes)
        parlay_recommendations.append({
            "legs": legs,
            "risk": risk,
            "payout": payout,
            "note": note
        })
    data = {
        "moneyline_picks": moneyline_picks,
        "parlay_recommendations": parlay_recommendations,
        "generated_at": str(datetime.now())
    }
    with open("data/bets_recommendations.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Bets data updated.")
