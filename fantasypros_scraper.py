import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def scrape_position_projections(position, filename):
    url = f'https://www.fantasypros.com/nfl/projections/{position}.php'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find('table', {'id': 'data'})
        rows = []
        for tr in table.tbody.find_all('tr'):
            tds = tr.find_all('td')
            if not tds or len(tds) < 8:
                continue
            # Extract player name and injury tag
            player_cell = tds[0]
            player_name = player_cell.find('a').text.strip() if player_cell.find('a') else player_cell.text.strip()
            injury_status = ''
            injury_tag = player_cell.find('span', class_='injury')
            if injury_tag:
                injury_status = injury_tag.text.strip()
            # Attempting to pull matchup color class
            opponent_cell = tds[1]
            matchup_class = opponent_cell.find('span', class_='fantasy-matchup')
            matchup_difficulty = 'Neutral'
            if matchup_class:
                cls = matchup_class.get('class', [])
                if 'green' in cls:
                    matchup_difficulty = 'Favorable'
                elif 'red' in cls:
                    matchup_difficulty = 'Tough'
                elif 'yellow' in cls:
                    matchup_difficulty = 'Moderate'
            # Build row dict (columns may differ by position)
            row = {
                'Player': player_name,
                'Team': player_cell.text.strip().split()[-1],
                'Opponent': opponent_cell.text.strip(),
                'Matchup Difficulty': matchup_difficulty,
                'Injury Status': injury_status,
            }
            # Add stat columns (grab all remaining columns generically)
            for i, td in enumerate(tds[2:], start=2):
                col_name = table.find_all('th')[i].text.strip() if i < len(table.find_all('th')) else f'Stat{i}'
                row[col_name] = td.text.strip()
            rows.append(row)
        df = pd.DataFrame(rows)
        os.makedirs('data', exist_ok=True)
        df.to_csv(f'data/{filename}', index=False)
        print(f"✅ {position.upper()} projections saved to data/{filename}")
    except Exception as e:
        print(f"⚠️ Error scraping {position.upper()} projections:", str(e))

def scrape_all_positions():
    scrape_position_projections('qb', 'qb_projections.csv')
    scrape_position_projections('rb', 'rb_projections.csv')
    scrape_position_projections('wr', 'wr_projections.csv')
    scrape_position_projections('te', 'te_projections.csv')
    scrape_position_projections('k', 'k_projections.csv')
    scrape_position_projections('dst', 'dst_projections.csv')

if __name__ == "__main__":
    scrape_all_positions()
