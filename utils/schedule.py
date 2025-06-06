import importlib.util
import os

scheduler_path = os.path.join(os.path.dirname(__file__), 'scheduler.py')
spec = importlib.util.spec_from_file_location('scheduler', scheduler_path)
scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduler)
should_use_real_data = scheduler.should_use_real_data

def get_upcoming_games():
    if should_use_real_data():
        # TO BE IMPLEMENTED: Real schedule fetching logic
        return []
    else:
        # Return mock schedule data for preview mode
        return [
            {"home": "MIA", "away": "LAC", "date": "2025-09-07", "stadium": "Hard Rock Stadium"},
            {"home": "KC", "away": "BUF", "date": "2025-09-07", "stadium": "Arrowhead Stadium"},
        ]
