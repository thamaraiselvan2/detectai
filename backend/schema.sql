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
    status TEXT DEFAULT 'UNREAD',  -- UNREAD, ACKNOWLEDGED, RESOLVED
    email_dispatched INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(protected_profile_id) REFERENCES protected_profiles(id) ON DELETE CASCADE,
    FOREIGN KEY(demo_profile_id) REFERENCES demo_profiles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- ─── Security Tables (Phase 1 Addition — additive, existing data untouched) ─

-- Tracks trusted devices per demo-social user (keyed by demo_profile username)
CREATE TABLE IF NOT EXISTS trusted_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,                 -- demo_profiles.id
    username TEXT NOT NULL,            -- demo_profiles.username
    device_fingerprint TEXT NOT NULL,  -- SHA256(User-Agent + /24 subnet)
    user_agent TEXT,
    ip_address TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_trusted INTEGER DEFAULT 0,      -- 0=pending verification, 1=trusted
    UNIQUE(username, device_fingerprint)
);

-- Full login event history for audit trail and IP/device signal analysis
CREATE TABLE IF NOT EXISTS login_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,                 -- demo_profiles.id
    username TEXT NOT NULL,
    registered_email TEXT,
    ip_address TEXT,
    device_fingerprint TEXT,
    user_agent TEXT,
    login_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verification_required INTEGER DEFAULT 0,
    verification_token TEXT,
    verification_expires_at DATETIME,
    verified INTEGER DEFAULT 0,
    verified_at DATETIME
);
