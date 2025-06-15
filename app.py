from flask import Flask, jsonify, request, redirect, url_for, render_template, session
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
from scrapers.yahoo_news import scrape_yahoo_news, get_yahoo_news_fallback
from scrapers.fantasypros_news import scrape_fantasypros_news
from scrapers.espn_news import scrape_espn_news
import difflib
import pytz
from utils.fantasy_scraper import scrape_fantasypros_rankings, scrape_yahoo_adp, cache_player_data, load_cached_data
from ranking_engine import generate_4dn_rankings
from caching.fantasy_cache import save_big_board_cache, load_cached_big_board
import atexit
from rankings_data import RANKINGS
import logging

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
# Schedule news refresh every 6 hours
scheduler.add_job(generate_bets_data, 'cron', hour='*/6', minute=5)  # Every 6 hours at HH:05
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
    today = datetime.now().date()
    week_1_date = datetime(2025, 9, 4).date()
    end_of_season = datetime(2025, 12, 29).date()  # adjust based on actual week 18 end

    if today < week_1_date:
        countdown_label = "Days Until NFL Kickoff"
        countdown_value = (week_1_date - today).days
    else:
        countdown_label = "Weeks Left in NFL Regular Season"
        total_weeks = 18
        weeks_passed = ((today - week_1_date).days) // 7
        countdown_value = max(total_weeks - weeks_passed, 0)

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
        countdown_label=countdown_label,
        countdown_value=countdown_value,
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

# --- Fantasy Chat API Route (Improved) ---
@app.route('/api/fantasy-chat', methods=['POST'])
def fantasy_chat():
    """
    Fantasy Assistant AI Chat endpoint. Now supports:
    - All fantasy football and NFL questions: draft strategy, player/team info, start/sit, trades, injuries, projections, etc.
    - Uses your algorithmic projections and data as context for more accurate, personalized answers.
    - Only answers football-related questions (fantasy or NFL).
    - Maintains a short conversation memory (last 3 exchanges) per user session for context.
    """
    data = request.get_json()
    user_message = data.get('message', '').strip() if data else ''
    if not user_message:
        return {"error": "No message provided."}, 400

    import re
    player_stats = []
    found_names = set()
    # Load all projections and rankings into a dict: {player_name: (position, row_dict)}
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
    # Try to find player names in the message
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

    # Conversation memory: store last 3 exchanges (6 messages) in session
    chat_history = session.get('chat_history', [])
    # Prepare Big Board and trending context for the system prompt
    top10 = [f"{p['name']} ({p['position']}, {p['team']})" for p in RANKINGS[:10]]
    # Try to get trending risers/fallers from the trending_players() function
    try:
        from flask import current_app
        with app.test_request_context():
            trending_resp = trending_players().get_json()
        risers = [f"{p['name']} ({p['position']}, +{p['change']})" for p in trending_resp.get('risers', [])]
        fallers = [f"{p['name']} ({p['position']}, {p['change']})" for p in trending_resp.get('fallers', [])]
    except Exception:
        risers = []
        fallers = []
    # Compose system prompt for GPT-4o
    system_prompt = (
        "You are 4DN Fantasy Assistant, an expert analytical coach for fantasy football and NFL, and a smart site guide. "
        "You ONLY answer questions about fantasy football, NFL, players, teams, draft strategy, projections, injuries, trades, and related topics, as well as questions about the 4DN Fantasy Football website and its features. "
        "You are deeply versed in all fantasy football formats (redraft, dynasty, best ball, DFS, IDP, superflex, etc.), scoring systems (PPR, half-PPR, standard, etc.), and advanced terminology (ADP, waiver wire, handcuff, sleeper, etc.). "
        "You know that Opening Day for the 2025 NFL season is September 4, 2025. If a user asks about Opening Day, explain what it is and when it is. "
        "You know the Season Pass is a one-time $9 purchase (pre-sale, normally $17) that unlocks all premium features on the site for the entire 2025 fantasy football season. It covers access to draft tools, rankings, AI chat, DFS tools, betting insights, and more, and expires at the end of the 2025 season. There are no recurring charges. "
        "If a user asks about the Season Pass, explain what it is, what it gives, how it works, and how to get it. "
        "You are also trained to answer most customer-related questions, such as how to sign up, how to log in, how to reset a password, how to use the Big Board, how to access features, and how to get support. Always provide clear, step-by-step instructions and be friendly and helpful. "
        "If a question is not about football, the website, or customer support, politely refuse.\n"
        "You have access to the user's custom algorithmic projections, rankings, and trending data.\n"
        f"Top 10 Big Board: {top10}\n"
        f"Top Risers: {risers}\n"
        f"Top Fallers: {fallers}\n"
        "Always use this data to inform your answers. Be specific, cite stats, and explain your reasoning.\n"
        "When giving advice, always explain your reasoning step-by-step, referencing the flow of your analysis or algorithm (e.g., how you weighed projections, matchups, trends, and format).\n"
        "For every answer, use a clear, structured format: start with a direct answer, then provide supporting details, and finish with a concise summary or actionable next step.\n"
        "For draft strategy, reference the Big Board and trending players. For player/team info, use projections and recent trends.\n"
        "If the user uses fantasy football terminology or abbreviations, always understand and clarify if needed.\n"
        "If the user asks about a feature, tool, or section of the site, provide a helpful walkthrough or explanation.\n"
        "If the user asks about Opening Day, the Season Pass, or how to use the site, answer with up-to-date, accurate, and friendly information.\n"
        "Respond in a professional, intelligent, and structured tone. For football questions, be analytical and coach-like. For site and customer support, be clear, friendly, and helpful.\n"
        "Keep answers friendly, clear, and actionable.\n"
        "All responses must be short and concise, with a maximum of 3 sentences."
    )
    try:
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        # Add up to last 6 messages (3 exchanges) from chat_history
        for msg in chat_history[-6:]:
            messages.append(msg)
        # Add the new user message as the last message
        messages.append({"role": "user", "content": user_message})
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = completion.choices[0].message.content.strip()
        # After getting reply, append both user and assistant messages to chat_history
        chat_history.append({'role': 'user', 'content': user_message})
        chat_history.append({'role': 'assistant', 'content': reply})
        # Only keep last 6 messages (3 exchanges)
        if len(chat_history) > 6:
            chat_history = chat_history[-6:]
        session['chat_history'] = chat_history
        if player_stats:
            reply = '\n'.join(player_stats) + '\n' + reply
        return {"response": reply}, 200
    except Exception as e:
        logging.exception("Error in /api/fantasy-chat")
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
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.7
                )
                ai_recommendation = response.choices[0].message.content.strip()
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
                    response = openai.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=80,
                        temperature=0.7
                    )
                    ai_recommendation = response.choices[0].message.content.strip()
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
            ai_recommendation = response.choices[0].message.content.strip()
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
    position = request.args.get('position', '')
    team = request.args.get('team', '')
    consistency = request.args.get('consistency', '')
    weather = request.args.get('weather', '')
    try:
        df = pd.read_csv("data/fake_player_rankings.csv")
        # Filtering logic
        if position:
            df = df[df['Position'] == position]
        if team:
            df = df[df['Team'] == team]
        if consistency:
            df = df[df['Consistency'] == consistency]
        if weather:
            df = df[df['WeatherProfile'] == weather]
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

@app.route('/auth', methods=['GET'])
def auth():
    # Show the combined login/signup page
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    print(f"[DEBUG] Login attempt for email: {email}")
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id, username, password, season_pass FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    print(f"[DEBUG] DB user row: {user}")
    conn.close()
    if user:
        print(f"[DEBUG] Checking password: {password} against hash: {user[2]}")
    if user and check_password_hash(user[2], password):
        print(f"[DEBUG] Login successful for user_id: {user[0]}")
        session['user_id'] = user[0]
        session['username'] = user[1]
        session['season_pass'] = bool(user[3])
        return redirect(url_for('account_dashboard'))
    else:
        print(f"[DEBUG] Invalid credentials for email: {email}")
        return render_template('auth.html', error='Invalid credentials.', error_type='login')

@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    print(f"[DEBUG] Signup attempt: username={username}, email={email}")
    if not username or not email or not password:
        print("[DEBUG] Signup failed: missing fields")
        return render_template('auth.html', error='All fields required.', error_type='signup')
    hashed_pw = generate_password_hash(password)
    print(f"[DEBUG] Hashed password: {hashed_pw}")
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_pw))
        conn.commit()
        conn.close()
        print(f"[DEBUG] Signup success for {email}")
        return render_template('auth.html', error='Account created! Please log in.', error_type='login')
    except sqlite3.IntegrityError:
        print(f"[DEBUG] Signup failed: username or email exists for {email}")
        return render_template('auth.html', error='Username or email already exists.', error_type='signup')

@app.route('/account')
def account_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username, email, season_pass FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    user = {
        'username': row[0],
        'email': row[1],
        'season_pass': bool(row[2]),
        'created_at': datetime.now(),  # For demo, not stored in DB
        'subscription': {'plan': 'Season Pass' if row[2] else 'None', 'active': bool(row[2]), 'next_billing': '--', 'can_switch': False},
        'payment_history': [
            {'date': '2025-06-01', 'amount': '$25.00', 'plan': 'Season Pass'} if row[2] else None
        ] if row[2] else []
    }
    return render_template('account_dashboard.html', user=user)

def get_live_4dn_big_board():
    # Scrape both sources
    fpros = scrape_fantasypros_rankings()
    yahoo = scrape_yahoo_adp()
    # Merge by name/team/position
    merged = {}
    for p in fpros:
        key = (p['name'].lower(), p['team'], p['position'])
        merged[key] = p.copy()
    for p in yahoo:
        key = (p['name'].lower(), p['team'], p['position'])
        if key in merged:
            merged[key]['yahoo_adp'] = p.get('yahoo_adp')
        else:
            merged[key] = p.copy()
    # Fill missing fields
    for v in merged.values():
        v.setdefault('fantasypros_rank', None)
        v.setdefault('yahoo_adp', None)
        v.setdefault('projected_points', 0)
        v.setdefault('sos', 5.0)
    # Generate 4DN rankings
    ranked = generate_4dn_rankings(list(merged.values()))
    return ranked

@app.route('/api/fantasy-big-board')
def get_4dn_board():
    position = request.args.get('position', None)
    # Filter by position if provided
    if position:
        filtered = [p for p in RANKINGS if p['position'].upper() == position.upper()]
    else:
        filtered = RANKINGS
    # Generate 4DN scores (rank-based)
    from ranking_engine import generate_4dn_rankings
    rankings = generate_4dn_rankings(filtered)
    return jsonify(rankings)

# --- Fantasy Football News API Route ---
@app.route('/api/news')
def api_news():
    """
    Returns a list of fantasy football news items as JSON.
    Now fetches live news from Yahoo Sports only, and always returns 7 items, using cached news if needed.
    """
    try:
        news_items = scrape_yahoo_news(max_items=20)
        if len(news_items) < 7:
            # Fill with cached news if available
            cached = get_yahoo_news_fallback(count=7-len(news_items))
            # Avoid duplicates
            seen = {n['headline'] for n in news_items}
            for n in cached:
                if n['headline'] not in seen:
                    news_items.append(n)
                if len(news_items) >= 7:
                    break
        news_items = news_items[:7]
        if not news_items:
            raise Exception("No news scraped")
    except Exception:
        # Fallback to cache only
        news_items = get_yahoo_news_fallback(count=7)
        if not news_items:
            # Final static fallback
            news_items = [
                {"headline": "Justin Jefferson returns to practice, expected to play Week 1", "summary": "Vikings star WR Justin Jefferson (hamstring) was a full participant in Thursday's practice.", "time": "2h ago", "url": ""},
                {"headline": "Bijan Robinson primed for breakout season", "summary": "Falcons RB Bijan Robinson has impressed coaches and is expected to see a heavy workload.", "time": "3h ago", "url": ""},
                {"headline": "Patrick Mahomes: 'We're ready to defend our title'", "summary": "Chiefs QB Patrick Mahomes says the team is focused and healthy heading into the opener.", "time": "4h ago", "url": ""},
                {"headline": "CMC remains top fantasy pick despite tough schedule", "summary": "Christian McCaffrey (SF) faces a challenging slate but remains the consensus 1.01.", "time": "5h ago", "url": ""},
                {"headline": "Injury update: Cooper Kupp questionable for Week 1", "summary": "Rams WR Cooper Kupp (hamstring) is questionable but making progress.", "time": "6h ago", "url": ""},
                {"headline": "NFL announces new kickoff rules for 2025 season", "summary": "The NFL has approved new kickoff rules aimed at player safety and more returns.", "time": "7h ago", "url": ""},
                {"headline": "Rookie QBs impress at minicamps", "summary": "Several rookie quarterbacks are turning heads in early team activities.", "time": "8h ago", "url": ""}
            ]
    return jsonify(news_items)

@app.route('/subscription')
def subscription():
    return render_template('subscription.html', stripe_public_key=os.getenv("STRIPE_PUBLIC_KEY"))

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': '4DN Lifetime Pass',
                },
                'unit_amount': 900,  # $9.00 in cents
            },
            'quantity': 1,
        }],
        success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('subscription', _external=True),
    )
    return redirect(session.url, code=303)

def scheduled_update():
    try:
        data = scrape_fantasypros_rankings()
        if data:
            cache_player_data(data)
            print("Fantasy data updated.")
    except:
        print("Update failed – using cached data.")

# Add schedule:
today = datetime(2025, 6, 4)
mid_july = datetime(2025, 7, 16)

if datetime.now() < mid_july:
    scheduler.add_job(scheduled_update, 'interval', days=14)
else:
    scheduler.add_job(scheduled_update, 'interval', days=2)

# Only call scheduler.start() once, after all jobs are added
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204

@app.route('/buy-season-pass', methods=['POST'])
def buy_season_pass():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Grant lifetime access by setting season_pass to 1 (true)
    c.execute('UPDATE users SET season_pass = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    session['season_pass'] = True
    # Optionally, add a payment record to payment_history (not implemented in DB)
    return redirect(url_for('account_dashboard'))

@app.route('/league-newsroom')
def league_newsroom():
    from utils.league_newsroom import generate_fake_news_data
    news_data = generate_fake_news_data(league_id="demo")  # Update later for real integrations
    return render_template("league_newsroom.html", news_data=news_data)

# Stripe webhook endpoint for payment events
import stripe
import sqlite3
from flask import request, jsonify

STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        customer_email = session_obj.get('customer_details', {}).get('email')
        if customer_email:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('UPDATE users SET season_pass = 1 WHERE email = ?', (customer_email,))
            conn.commit()
            conn.close()
    return jsonify({'status': 'success'})

@app.route('/debug-users')
def debug_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id, username, email, password, season_pass FROM users')
    users = c.fetchall()
    conn.close()
    html = '<h2>All Users in DB</h2><table border=1><tr><th>ID</th><th>Username</th><th>Email</th><th>Password Hash</th><th>Season Pass</th></tr>'
    for u in users:
        html += f'<tr><td>{u[0]}</td><td>{u[1]}</td><td>{u[2]}</td><td>{u[3]}</td><td>{u[4]}</td></tr>'
    html += '</table>'
    return html

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
