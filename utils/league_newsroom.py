import json, datetime

def generate_fake_news_data(league_id):
    return {
        "headlines": [
            f"{datetime.date.today().strftime('%B %d')} – The trade heard 'round the league! Team A ships CMC to Team B in a blockbuster deal!",
            "BREAKING: Team C drops $32 of FAAB on a backup TE. Desperation or genius?",
            "Rivalry Renewed: Team D vs Team E showdown headlines Week 3!"
        ],
        "transactions": [
            {"type": "Trade", "details": "Team A traded Christian McCaffrey to Team B for DeVonta Smith and a 2026 pick."},
            {"type": "Add", "details": "Team C added Dalton Schultz (TE - HOU)."},
            {"type": "Drop", "details": "Team F dropped Jimmy Garoppolo (QB - FA)."}
        ],
        "matchups": [
            {"week": 3, "spotlight": "Team D and Team E both sit at 2-0. This could determine early playoff seeding."}
        ]
    }
