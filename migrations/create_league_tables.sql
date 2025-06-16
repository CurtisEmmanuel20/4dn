-- leagues table: stores league info
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    api_key TEXT,
    owner_id INTEGER,
    share_code TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- user_leagues table: many-to-many user/league relationship
CREATE TABLE IF NOT EXISTS user_leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    league_id INTEGER,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
