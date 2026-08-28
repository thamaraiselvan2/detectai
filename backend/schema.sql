-- Schema for Fake Profile & Impersonation Detection System

CREATE TABLE IF NOT EXISTS protected_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    follower_count INTEGER DEFAULT 0,
    is_monitoring_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demo_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password TEXT,
    bio TEXT,
    avatar_url TEXT,
    followers_count INTEGER DEFAULT 0,
    following_count INTEGER DEFAULT 0,
    posts_count INTEGER DEFAULT 0,
    account_age_days INTEGER DEFAULT 30,
    is_verified INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registered_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    original_profile_id INTEGER NOT NULL,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(original_profile_id) REFERENCES demo_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS impersonation_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registered_profile_id INTEGER NOT NULL,
    demo_profile_id INTEGER NOT NULL,
    risk_score INTEGER NOT NULL,
    classification TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    email_status TEXT NOT NULL DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    emailed_at DATETIME,
    UNIQUE(registered_profile_id, demo_profile_id),
    FOREIGN KEY(registered_profile_id) REFERENCES registered_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(demo_profile_id) REFERENCES demo_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS check_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_username TEXT NOT NULL,
    matched_protected_id INTEGER,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    factors_json TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(matched_protected_id) REFERENCES protected_profiles(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protected_profile_id INTEGER NOT NULL,
    demo_profile_id INTEGER NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    reason_summary TEXT NOT NULL,
    status TEXT DEFAULT 'UNREAD', -- UNREAD, ACKNOWLEDGED, RESOLVED
    email_dispatched INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(protected_profile_id) REFERENCES protected_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(demo_profile_id) REFERENCES demo_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
