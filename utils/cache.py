import time

_cache = {}

def cache_data(key, data, ttl=14400):  # 4-hour default cache
    _cache[key] = {"data": data, "timestamp": time.time(), "ttl": ttl}

def get_cached_data(key):
    if key in _cache:
        cached = _cache[key]
        if time.time() - cached["timestamp"] < cached["ttl"]:
            return cached["data"]
    return None
