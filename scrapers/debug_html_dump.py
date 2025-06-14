import requests

# Dump HTML for FantasyPros
fp_url = "https://www.fantasypros.com/nfl/news.php"
fp_resp = requests.get(fp_url)
with open("fantasypros_news_dump.html", "w", encoding="utf-8") as f:
    f.write(fp_resp.text)

# Dump HTML for ESPN
espn_url = "https://www.espn.com/nfl/"
espn_resp = requests.get(espn_url)
with open("espn_news_dump.html", "w", encoding="utf-8") as f:
    f.write(espn_resp.text)

print("HTML dumps complete.")
