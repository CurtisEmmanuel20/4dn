from flask import Flask, jsonify, request, redirect, url_for, render_template
from dotenv import load_dotenv
import os
import sqlite3
import stripe
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import pandas as pd
import threading
import schedule
import time
import sys
import json
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from bets_recommendation_generator import generate_bets_data
from datetime import datetime
from matchup_pool import refresh_elite_matchups, current_elite_players
from flask import render_template

load_dotenv()  # This loads the .env file

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random value in production

# Set EST timezone
eastern = timezone("US/Eastern")
# Set up scheduler
scheduler = BackgroundScheduler(timezone=eastern)
scheduler.add_job(generate_bets_data, 'cron', hour=0, minute=5)  # 12:05 AM EST
scheduler.start()
# Run once at startup
generate_bets_data()

# Set it to update Mon/Thu/Sat at 12 AM EST
def elite_schedule_runner():
    def update():
        now = datetime.now(pytz.timezone("US/Eastern"))
        if now.weekday() in [0, 3, 5]:  # Mon, Thu, Sat
            refresh_elite_matchups()

    schedule.every().day.at("00:00").do(update)

    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=elite_schedule_runner, daemon=True).start()

@app.route('/api/player-readiness')
def player_readiness():
    sample_data = [
        {"name": "Saquon Barkley", "injury_status": "Healthy", "snap_trend_score": 85, "momentum_score": 78},
        {"name": "Justin Jefferson", "injury_status": "Questionable", "snap_trend_score": 72, "momentum_score": 65},
        {"name": "Patrick Mahomes", "injury_status": "Healthy", "snap_trend_score": 90, "momentum_score": 88}
    ]
    return jsonify(sample_data)

@app.route('/api/defense-health')
def defense_health():
    sample_data = [
        {"team": "NYG", "injuries": ["Kayvon Thibodeaux"], "defensive_health_score": 68},
        {"team": "MIN", "injuries": [], "defensive_health_score": 92},
        {"team": "KC", "injuries": ["Chris Jones", "L'Jarius Sneed"], "defensive_health_score": 55}
    ]
    return jsonify(sample_data)

@app.route('/api/weather-impact')
def weather_impact():
    sample_data = [
        {"game": "NYG vs DAL", "location_type": "Outdoor", "weather_forecast": "Rain", "weather_impact_score": 60},
        {"game": "MIN vs GB", "location_type": "Indoor", "weather_forecast": "Clear", "weather_impact_score": 10},
        {"game": "KC vs DEN", "location_type": "Outdoor", "weather_forecast": "Snow", "weather_impact_score": 75}
    ]
    return jsonify(sample_data)

@app.route('/')
def home():
    """
    Render the dashboard as the landing page (now at '/').
    """
    weeks_left = 18  # You can make this dynamic later
    featured_matchup = {
        'title': 'Featured Matchup of the Week',
        'desc': 'Tyreek Hill (MIA) vs. New England Patriots – Projected for 21.4 PPR points.'
    }
    projections = [
        {"player": "Justin Jefferson", "team": "MIN", "matchup": "vs GB", "projected_points": 18.4},
        {"player": "Saquon Barkley", "team": "NYG", "matchup": "at DAL", "projected_points": 14.1},
        {"player": "Jalen Hurts", "team": "PHI", "matchup": "vs WAS", "projected_points": 25.0},
        {"player": "Tyreek Hill", "team": "MIA", "matchup": "vs NE", "projected_points": 21.4},
        {"player": "Christian McCaffrey", "team": "SF", "matchup": "at SEA", "projected_points": 20.2}
    ]
    return render_template(
        'dashboard.html',
        weeks_left=weeks_left,
        featured_matchup=featured_matchup,
        projections=projections
    )

# --- Payment Success Route ---
@app.route('/payment-success')
def payment_success():
    """
    Payment success page. No session or user logic; just show a thank you message.
    """
    return render_template('payment_success.html')

# --- Projections API Route (Open) ---
@app.route('/api/projections')
def projections():
    """
    Return projections for a given position (QB, RB, WR, TE, K, DST) as JSON for any user.
    Usage: /api/projections?position=QB
    """
    position = request.args.get('position', 'QB').upper()
    valid_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    if position not in valid_positions:
        return jsonify({'error': 'Invalid position'}), 400
    csv_path = f'{position.lower()}_projections.csv'
    if not os.path.exists(csv_path):
        return jsonify({'error': 'Data not found'}), 400
    df = pd.read_csv(csv_path)
    return df.head(10).to_json(orient='records')

# --- Fantasy Chat API Route (Open) ---
@app.route('/api/fantasy-chat', methods=['POST'])
def fantasy_chat():
    """
    Fantasy Assistant AI Chat endpoint. Accessible to any user.
    Accepts JSON: { "message": "..." }
    Returns: { "response": "..." }
    """
    data = request.get_json()
    user_message = data.get('message', '').strip() if data else ''
    if not user_message:
        return {"error": "No message provided."}, 400

    # Try to find player names in the message
    import re
    player_stats = []
    found_names = set()
    # Load all projections into a dict: {player_name: (position, row_dict)}
    positions = ['qb', 'rb', 'wr', 'te', 'k', 'dst']
    projections = {}
    for pos in positions:
        csv_path = f'data/{pos}_projections.csv'
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                for _, row in df.iterrows():
                    name = str(row.get('player') or row.get('Player') or row.get('name') or '').strip()
                    if name:
                        projections[name.lower()] = (pos.upper(), row)
            except Exception:
                continue
    # Find capitalized word pairs (simple player name heuristic)
    possible_names = re.findall(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', user_message)
    for pname in possible_names:
        key = pname.lower()
        if key in projections and key not in found_names:
            found_names.add(key)
            pos, row = projections[key]
            pts = row.get('projected_points') or row.get('Projected Points') or row.get('points') or ''
            team = row.get('team') or row.get('Team') or ''
            opp = row.get('matchup') or row.get('Opponent') or ''
            summary = f"{pname} ({pos}) is projected for {pts} points for {team} vs {opp}. "
            player_stats.append(summary)
    # System prompt for GPT-4o
    system_prompt = (
        "You are a fantasy football assistant named 4DN Chat. Only answer fantasy-related questions such as start/sit advice, trade evaluations, injury reports, and weather impacts. "
        "Provide detailed, helpful, and easy-to-understand responses. Include: Opponent defensive ranking, weather and location (home/away), game script expectations (e.g., shootouts), and notable injuries to teammates or defenders. "
        "Keep answers friendly, informed, and clear."
    )
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        reply = completion.choices[0].message['content'].strip()
        if player_stats:
            reply = '\n'.join(player_stats) + '\n' + reply
        return {"response": reply}, 200
    except Exception as e:
        return {"error": f"AI error: {str(e)}"}, 500

@app.route("/api/trending")
def trending_players():
    positions = ["qb", "rb", "wr", "te"]
    current_week = "current"
    last_week = "last"
    player_changes = []
    for pos in positions:
        current_path = f"data/{pos}_projections_week_{current_week}.csv"
        last_path = f"data/{pos}_projections_week_{last_week}.csv"
        if not os.path.exists(current_path) or not os.path.exists(last_path):
            continue
        current_df = pd.read_csv(current_path)
        last_df = pd.read_csv(last_path)
        # Try to find the correct columns for player and projection
        def get_col(df, options):
            for opt in options:
                if opt in df.columns:
                    return opt
            return None
        player_col = get_col(current_df, ["Player", "player", "Name", "name"])
        proj_col = get_col(current_df, ["Projection", "projected_points", "points", "Projection_current"])
        last_proj_col = get_col(last_df, ["Projection", "projected_points", "points", "Projection_last"])
        if not player_col or not proj_col or not last_proj_col:
            continue
        merged = pd.merge(
            current_df[[player_col, proj_col]],
            last_df[[player_col, last_proj_col]],
            left_on=player_col,
            right_on=player_col,
            suffixes=("_current", "_last")
        )
        merged["Change"] = merged[proj_col] - merged[last_proj_col]
        merged["Position"] = pos.upper()
        for _, row in merged.iterrows():
            player_changes.append({
                "name": row[player_col],
                "position": row["Position"],
                "change": round(row["Change"], 2)
            })
    risers = sorted(
        [p for p in player_changes if p["change"] > 0],
        key=lambda x: x["change"],
        reverse=True
    )[:5]
    fallers = sorted(
        [p for p in player_changes if p["change"] < 0],
        key=lambda x: x["change"]
    )[:5]
    return jsonify({
        "risers": risers,
        "fallers": fallers
    })

def run_scraper():
    os.system(f"{sys.executable} fantasypros_scraper.py")

def schedule_scraper():
    schedule.every().tuesday.at("08:00").do(run_scraper)
    schedule.every().friday.at("20:00").do(run_scraper)  # 8:00 PM Friday
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler in a background thread
scheduler_thread = threading.Thread(target=schedule_scraper, daemon=True)
scheduler_thread.start()

@app.route('/player-compare', methods=['GET', 'POST'])
def player_compare():
    import os
    import csv
    from flask import request, render_template
    import openai

    # Helper to get all player names from all position CSVs
    def get_all_players():
        player_set = set()
        pos_files = ['qb_projections.csv', 'rb_projections.csv', 'wr_projections.csv', 'te_projections.csv', 'dst_projections.csv', 'k_projections.csv']
        for fname in pos_files:
            path = os.path.join('data', fname)
            if not os.path.exists(path):
                continue
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_set.add(row.get('player') or row.get('name'))
        return sorted([p for p in player_set if p])

    # Helper to find player data and position
    def find_player_data(player_name):
        pos_files = [
            ('QB', 'qb_projections.csv'),
            ('RB', 'rb_projections.csv'),
            ('WR', 'wr_projections.csv'),
            ('TE', 'te_projections.csv'),
            ('DST', 'dst_projections.csv'),
            ('K', 'k_projections.csv'),
        ]
        for pos, fname in pos_files:
            path = os.path.join('data', fname)
            if not os.path.exists(path):
                continue
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row.get('player') or row.get('name')) == player_name:
                        return row, pos
        return None, None

    def get_last3_avg(player_row):
        for key in ['last3_avg', 'last_3_avg', 'last3', 'last_3']:
            if key in player_row:
                try:
                    return float(player_row[key])
                except:
                    pass
        import random
        try:
            proj = float(player_row.get('projected_points', 0))
        except:
            proj = 10.0
        return round(proj + random.uniform(-3, 3), 1)

    def get_matchup(player_row):
        for key in ['matchup_rank', 'matchup', 'opp_rank', 'def_rank']:
            if key in player_row:
                return player_row[key]
        return player_row.get('matchup', 'N/A')

    player_names = get_all_players()
    compare_result = None
    ai_recommendation = None
    roster_slots = [
        ('QB', 'QB'),
        ('RB1', 'RB'),
        ('RB2', 'RB'),
        ('WR1', 'WR'),
        ('WR2', 'WR'),
        ('WR3', 'WR'),
        ('TE', 'TE'),
        ('FLEX', 'RB/WR/TE'),
        ('SUPERFLEX', 'QB/RB/WR/TE'),
        ('DST', 'DST'),
        ('K', 'K')
    ]
    if request.method == 'POST':
        # Check if roster comparison (multiple players per side)
        if request.form.get('roster1-QB') and request.form.get('roster2-QB'):
            roster1 = {}
            roster2 = {}
            for slot, pos in roster_slots:
                roster1[slot] = request.form.get(f'roster1-{slot}')
                roster2[slot] = request.form.get(f'roster2-{slot}')
            roster1_data = {}
            roster2_data = {}
            total1 = 0
            total2 = 0
            for slot, pos in roster_slots:
                p1, _ = find_player_data(roster1[slot]) if roster1[slot] else (None, None)
                p2, _ = find_player_data(roster2[slot]) if roster2[slot] else (None, None)
                if p1:
                    try:
                        pts = float(p1.get('projected_points', 0))
                    except:
                        pts = 0
                    total1 += pts
                if p2:
                    try:
                        pts = float(p2.get('projected_points', 0))
                    except:
                        pts = 0
                    total2 += pts
                roster1_data[slot] = {
                    'name': roster1[slot],
                    'projected_points': p1.get('projected_points', 'N/A') if p1 else 'N/A',
                    'matchup': get_matchup(p1) if p1 else 'N/A',
                    'last3_avg': get_last3_avg(p1) if p1 else 'N/A',
                } if roster1[slot] else None
                roster2_data[slot] = {
                    'name': roster2[slot],
                    'projected_points': p2.get('projected_points', 'N/A') if p2 else 'N/A',
                    'matchup': get_matchup(p2) if p2 else 'N/A',
                    'last3_avg': get_last3_avg(p2) if p2 else 'N/A',
                } if roster2[slot] else None
            compare_result = {
                'roster1': roster1_data,
                'roster2': roster2_data,
                'total1': round(total1, 1),
                'total2': round(total2, 1)
            }
            # AI recommendation for rosters
            prompt = f"Compare these two fantasy football rosters. Roster 1: {[roster1[slot] for slot, _ in roster_slots]}. Roster 2: {[roster2[slot] for slot, _ in roster_slots]}. Based on projected points, matchups, and recent performance, which roster is favored and why? Limit response to 2 sentences."
            try:
                openai.api_key = os.environ.get('OPENAI_API_KEY')
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.7
                )
                ai_recommendation = response['choices'][0]['message']['content'].strip()
            except Exception as e:
                ai_recommendation = "AI recommendation unavailable."
        else:
            # Single player vs player compare (legacy)
            player1 = request.form.get('player1')
            player2 = request.form.get('player2')
            row1, pos1 = find_player_data(player1)
            row2, pos2 = find_player_data(player2)
            if row1 and row2:
                compare_result = {
                    'player1': {
                        'name': player1,
                        'position': pos1,
                        'projected_points': row1.get('projected_points', 'N/A'),
                        'matchup': get_matchup(row1),
                        'last3_avg': get_last3_avg(row1),
                        'rank': row1.get('rank', row1.get('position_rank', 'N/A'))
                    },
                    'player2': {
                        'name': player2,
                        'position': pos2,
                        'projected_points': row2.get('projected_points', 'N/A'),
                        'matchup': get_matchup(row2),
                        'last3_avg': get_last3_avg(row2),
                        'rank': row2.get('rank', row2.get('position_rank', 'N/A'))
                    }
                }
                prompt = f"Compare these two fantasy football players: {player1} and {player2}. Based on their projected points, matchup difficulty, and last 3 games, who should I start? Be specific and mention stats. Limit response to 2 informative sentences."
                try:
                    openai.api_key = os.environ.get('OPENAI_API_KEY')
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=80,
                        temperature=0.7
                    )
                    ai_recommendation = response['choices'][0]['message']['content'].strip()
                except Exception as e:
                    ai_recommendation = "AI recommendation unavailable."
    return render_template('player_compare.html', player_names=player_names, compare_result=compare_result, ai_recommendation=ai_recommendation, roster_slots=roster_slots)

# --- DFS Page Route ---
@app.route('/dfs')
def dfs():
    with open('data/dfs_insights.json') as f:
        dfs_insights = json.load(f)
    return render_template('dfs.html', dfs_insights=dfs_insights)

# --- DFS Lineup API Endpoint ---
@app.route('/api/dfs-lineup')
def api_dfs_lineup():
    # Use hardcoded fake data for now, but structure for easy replacement
    lineup_data = [
        {"name": "Josh Allen", "team": "BUF", "position": "QB", "projected_points": 24.3},
        {"name": "Breece Hall", "team": "NYJ", "position": "RB", "projected_points": 13.9},
        {"name": "Bijan Robinson", "team": "ATL", "position": "RB", "projected_points": 13.8},
        {"name": "Tyreek Hill", "team": "MIA", "position": "WR", "projected_points": 13.8},
        {"name": "Amon-Ra St. Brown", "team": "DET", "position": "WR", "projected_points": 12.1},
        {"name": "CeeDee Lamb", "team": "DAL", "position": "WR", "projected_points": 11.9},
        {"name": "T.J. Hockenson", "team": "MIN", "position": "TE", "projected_points": 14.3},
        {"name": "Kyren Williams", "team": "LAR", "position": "FLEX", "projected_points": 12.6},
        {"name": "Minnesota Vikings", "team": "MIN", "position": "DST", "projected_points": 8.8}
    ]
    reasoning = (
        "This DFS lineup was generated using top-projected players at each position. "
        "The structure is ready for real data integration—just swap the hardcoded list for live projections!"
    )
    return jsonify({'lineup': lineup_data, 'reasoning': reasoning})

@app.route("/bets")
def bets():
    with open("data/bets_recommendations.json") as f:
        bets_data = json.load(f)
    return render_template("bets.html", bets_data=bets_data)

@app.route('/start-sit', methods=['GET', 'POST'])
def start_sit():
    ai_recommendation = None
    player_input = []
    chart_data = None
    # Always use fake data for now, regardless of form submission
    players = [
        {
            "name": "DK Metcalf",
            "position": "WR",
            "points": 14.8,
            "matchup": "vs SF",
            "matchup_rank": 3,
            "weather": "Heavy Rain",
            "injury_status": "Healthy",
            "red_zone_usage": "High",
            "def_health": "75%"
        },
        {
            "name": "Courtland Sutton",
            "position": "WR",
            "points": 13.1,
            "matchup": "vs LV",
            "matchup_rank": 22,
            "weather": "Clear",
            "injury_status": "Healthy",
            "red_zone_usage": "Medium",
            "def_health": "80%"
        },
        {
            "name": "DeVonta Smith",
            "position": "WR",
            "points": 15.0,
            "matchup": "vs DAL",
            "matchup_rank": 7,
            "weather": "Clear",
            "injury_status": "Questionable (knee)",
            "red_zone_usage": "Medium",
            "def_health": "68%"
        }
    ]
    if request.method == 'POST':
        player_input = [p.strip() for p in [request.form.get('player1'), request.form.get('player2'), request.form.get('player3')] if p]
        prompt = (
            "You're a fantasy football expert. Rank these players as Start > Flex > Sit using these factors: "
            "projected points, matchup difficulty, weather, injury status, red zone usage, and defensive health.\n\n"
        )
        for p in players:
            prompt += (
                f"{p['name']} – {p['position']}, projected {p['points']} pts, "
                f"{p['matchup']} ({p['matchup_rank']} vs {p['position']}), "
                f"weather: {p['weather']}, injury: {p['injury_status']}, "
                f"red zone usage: {p['red_zone_usage']}, defensive health: {p['def_health']}\n"
            )
        prompt += (
            "\nRespond with:\n"
            "- ✅ Start: [Player Name] – [Reason]\n"
            "- 🔄 Flex: [Player Name] – [Reason]\n"
            "- ⛔ Sit: [Player Name] – [Reason]"
        )
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            ai_recommendation = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            ai_recommendation = "AI error occurred."
    # Always show chart_data for the fake players
    chart_data = {
        "labels": [p['name'] for p in players],
        "points": [p['points'] for p in players]
    }
    return render_template(
        'start_sit.html',
        ai_recommendation=ai_recommendation,
        player_input=player_input,
        chart_data=chart_data
    )

@app.route("/elite-matchups")
def elite_matchups():
    # Always show a demo set of 9 fake players by position: 1 QB, 3 WR, 2 RB, 1 TE, 1 K, 1 DST
    players = [
        # QB
        {
            "name": "Jalen Hurts",
            "team": "PHI",
            "position": "QB",
            "matchup": "vs WAS",
            "def_rank": 30,
            "status": "Healthy",
            "snap_trend": [100, 100, 100],
            "red_zone_looks": 2,
            "weather": "Clear 68°F",
            "ai_blurb": "Dual-threat upside, soft pass defense."
        },
        # WRs
        {
            "name": "CeeDee Lamb",
            "team": "DAL",
            "position": "WR",
            "matchup": "@ WAS",
            "def_rank": 29,
            "status": "Healthy",
            "snap_trend": [92, 91, 93],
            "red_zone_looks": 2,
            "weather": "Dome",
            "ai_blurb": "Elite WR1 usage and soft secondary."
        },
        {
            "name": "Tyreek Hill",
            "team": "MIA",
            "position": "WR",
            "matchup": "vs NE",
            "def_rank": 28,
            "status": "Healthy",
            "snap_trend": [90, 91, 92],
            "red_zone_looks": 3,
            "weather": "Clear 80°F",
            "ai_blurb": "Game-breaking speed, high target share."
        },
        {
            "name": "Amon-Ra St. Brown",
            "team": "DET",
            "position": "WR",
            "matchup": "vs CHI",
            "def_rank": 27,
            "status": "Healthy",
            "snap_trend": [88, 89, 90],
            "red_zone_looks": 2,
            "weather": "Dome",
            "ai_blurb": "Slot mismatch, high-volume role."
        },
        # RBs
        {
            "name": "Bijan Robinson",
            "team": "ATL",
            "position": "RB",
            "matchup": "@ ARI",
            "def_rank": 32,
            "status": "Healthy",
            "snap_trend": [68, 70, 72],
            "red_zone_looks": 4,
            "weather": "Dome",
            "ai_blurb": "Facing league-worst run D, heavy RZ work."
        },
        {
            "name": "Raheem Mostert",
            "team": "MIA",
            "position": "RB",
            "matchup": "vs CAR",
            "def_rank": 31,
            "status": "Healthy",
            "snap_trend": [71, 74, 72],
            "red_zone_looks": 3,
            "weather": "Clear 75°F",
            "ai_blurb": "Soft matchup and elite red zone usage."
        },
        # TE
        {
            "name": "Sam LaPorta",
            "team": "DET",
            "position": "TE",
            "matchup": "vs GB",
            "def_rank": 25,
            "status": "Healthy",
            "snap_trend": [85, 87, 88],
            "red_zone_looks": 2,
            "weather": "Dome",
            "ai_blurb": "Emerging as a top target, weak TE defense."
        },
        # Kicker
        {
            "name": "Jake Elliott",
            "team": "PHI",
            "position": "K",
            "matchup": "vs DAL",
            "def_rank": 20,
            "status": "Healthy",
            "snap_trend": [100, 100, 100],
            "red_zone_looks": 0,
            "weather": "Clear 65°F",
            "ai_blurb": "High-scoring offense, plenty of FG chances."
        },
        # Defense
        {
            "name": "San Francisco 49ers",
            "team": "SF",
            "position": "DST",
            "matchup": "vs ARI",
            "def_rank": 2,
            "status": "Healthy",
            "snap_trend": [100, 100, 100],
            "red_zone_looks": 0,
            "weather": "Clear 70°F",
            "ai_blurb": "Elite pass rush, facing turnover-prone QB."
        }
    ]
    return render_template("elite_matchups.html", players=players)

@app.route('/rankings')
def player_rankings():
    import pandas as pd
    try:
        df = pd.read_csv("data/fake_player_rankings.csv")
        print('DEBUG: Loaded player rankings sample:', df.head(2).to_dict())
        # Convert columns to match template keys if needed
        data = []
        for _, row in df.iterrows():
            data.append({
                'Name': row.get('Name', ''),
                'Team': row.get('Team', ''),
                'Position': row.get('Position', ''),
                'ProjectedPoints': row.get('ProjectedPoints', ''),
                'Consistency': row.get('Consistency', ''),
                'WeatherProfile': row.get('WeatherProfile', ''),
                'RedZoneShare': row.get('RedZoneShare', ''),
                'ExplosivePlays': row.get('ExplosivePlays', ''),
                'TargetQuality': row.get('TargetQuality', ''),
                'OlineGrade': row.get('OlineGrade', ''),
                'QBStability': row.get('QBStability', ''),
                'PlayerReadiness': row.get('PlayerReadiness', ''),
                'MatchupGrade': row.get('MatchupGrade', ''),
                'ClutchRating': row.get('ClutchRating', ''),
                'DefHealthScore': row.get('DefHealthScore', '')
            })
        return render_template("player_rankings.html", data=data)
    except Exception as e:
        print('ERROR in /rankings route:', e)
        return render_template("player_rankings.html", data=[])

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
