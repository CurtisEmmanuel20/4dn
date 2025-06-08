# 4DN Fantasy Football Platform

## Overview
4DN Fantasy Football is a modern, data-driven fantasy football analytics and management platform. It combines proprietary player rankings, advanced projections, AI-powered chat, and a user-friendly web interface to give fantasy managers a true analytical edge. The platform supports account management, subscriptions, a fantasy big board, DFS tools, league newsroom, and more.

## Features
- **Modern Account System**: Unified login/signup, account dashboard, and subscription management.
- **Static Player Rankings**: Fast, reliable big board with position filtering and proprietary 4DN Score.
- **AI Fantasy Assistant**: GPT-4o-powered chat for fantasy advice and site support, with short-term memory.
- **Season Pass**: Lifetime access via a one-time $9 Summer Pre-Sale (no recurring fees).
- **League Newsroom**: AI-generated headlines, transaction tracker, matchup spotlights, and league standings.
- **DFS & Betting Tools**: Optimized lineups, prop bet suggestions, and advanced analytics (for Season Pass holders).
- **Modern UI**: Responsive, compact cards, tooltips, banners, and modal overlays for a seamless experience.
- **Logout Everywhere**: Secure session management and easy logout from any page.

## Tech Stack
- **Backend**: Python, Flask, Flask-RESTful, SQLite
- **Frontend**: HTML, Bootstrap 5, JavaScript
- **AI/ML**: OpenAI GPT-4o (for chat), custom ranking/analytics engines
- **Other**: BeautifulSoup4 (for news scraping), Requests

## Project Structure
- `app.py` — Main Flask app (routes, API, session, chat, etc.)
- `rankings_data.py` — Static player rankings
- `ranking_engine.py` — 4DN score logic
- `templates/` — HTML templates (dashboard, account, newsroom, etc.)
- `scrapers/` — News scraping scripts
- `caching/` — Caching logic for news/data
- `utils/` — Utility scripts (newsroom data, etc.)
- `users.db` — SQLite user database
- `requirements.txt` — Python dependencies

## Quick Start
1. **Clone the repo**
   ```sh
   git clone <your-repo-url>
   cd 4dn-fantasy-football
   ```
2. **Set up a virtual environment (optional but recommended)**
   ```sh
   python -m venv env
   env\Scripts\activate  # On Windows
   # or
   source env/bin/activate  # On Mac/Linux
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
4. **Initialize the database**
   ```sh
   python init_db.py
   ```
5. **Run the app**
   ```sh
   python app.py
   ```
6. **Open in your browser**
   - Visit [http://localhost:5000](http://localhost:5000)

## Usage
- **Sign up/Login**: Use the unified `/auth` page.
- **Account Management**: Access via the "My Account" button in the header.
- **Get Season Pass**: Purchase via the dashboard or account page for lifetime access.
- **Big Board**: View and filter top 100 player rankings by position.
- **AI Chat**: Ask fantasy or site questions in the chat box.
- **League Newsroom**: Access via sidebar for league headlines, transactions, and standings.

## Customization & Development
- Edit `rankings_data.py` to update player rankings.
- Modify templates in `templates/` for UI changes.
- Extend backend logic in `app.py` for new features.
- Add new scrapers or data sources in `scrapers/`.

## Contributing
Pull requests and issues are welcome! Please open an issue to discuss major changes first.

## License
This project is for demonstration and personal use. For commercial use, please contact the author.

---

**4DN Fantasy Football** — Modern analytics for serious fantasy managers.