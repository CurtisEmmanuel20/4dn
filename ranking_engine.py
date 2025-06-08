from typing import List, Dict
import math
import random

def generate_4dn_rankings(data: List[Dict]) -> List[Dict]:
    """
    Given a merged list of player dicts (with fantasypros_rank, yahoo_adp, projected_points, sos, etc),
    generate a 4DN score and return a sorted list with all required metadata.
    """
    rankings = []
    for i, player in enumerate(data):
        score = 100 - i * 0.75  # basic decay formula
        rankings.append({
            "rank": i + 1,
            "name": player["name"],
            "team": player["team"],
            "position": player["position"],
            "4dn_score": round(score, 2)
        })
    return rankings
