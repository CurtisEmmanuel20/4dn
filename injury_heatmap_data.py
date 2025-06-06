teams = [
    "49ers", "Chiefs", "Ravens", "Eagles", "Bills", "Cowboys", "Dolphins", "Bengals", 
    "Lions", "Seahawks", "Jets", "Browns", "Chargers", "Jaguars", "Vikings", "Packers", 
    "Steelers", "Saints", "Falcons", "Texans", "Colts", "Broncos", "Bucs", "Commanders", 
    "Bears", "Raiders", "Panthers", "Giants", "Titans", "Patriots", "Rams", "Cardinals"
]

position_groups = ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"]

# The following fake_heatmap_data is deprecated and should be replaced with live data from Yahoo/ESPN/Twitter APIs.
# import random
# fake_heatmap_data = []
# for team in sorted(teams):
#     row = {"team": team}
#     for pos in position_groups:
#         row[pos] = random.choice([0, 1, 2])  # 0: healthy, 1: caution, 2: injured
#     fake_heatmap_data.append(row)
# TODO: Implement live injury heatmap data using real sources (Yahoo, ESPN, Twitter/X, etc.)
