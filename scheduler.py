import schedule
import time
import os

def run_scraper():
    os.system("python fantasypros_scraper.py")

# Schedule: Tuesday 8 AM & Friday 8 PM EST
schedule.every().tuesday.at("08:00").do(run_scraper)
schedule.every().friday.at("20:00").do(run_scraper)

while True:
    schedule.run_pending()
    time.sleep(60)
