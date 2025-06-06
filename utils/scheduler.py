from datetime import date

LAUNCH_DATE = date(2025, 7, 16)

def should_use_real_data():
    return date.today() >= LAUNCH_DATE
