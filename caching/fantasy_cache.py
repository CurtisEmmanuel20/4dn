import json
import os

def save_big_board_cache(data, path="caching/fantasy_cache.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)

def load_cached_big_board(path="caching/fantasy_cache.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)
