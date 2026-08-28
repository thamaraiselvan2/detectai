from database import get_db, query_db

PROTECTED_SEED_PROFILES = [
    {
        "username": "elonmusk",
        "display_name": "Elon Musk",
        "email": "contact@x.corp.internal",
        "bio": "CEO of Tesla, SpaceX, xAI & CTO of X. Exploring the universe and accelerating sustainable energy.",
        "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&auto=format&fit=crop&q=80",
        "follower_count": 180000000,
        "is_monitoring_active": 1
    },
    {
        "username": "satyanadella",
        "display_name": "Satya Nadella",
        "email": "satya@microsoft.internal",
        "bio": "Chairman and CEO of Microsoft. Passionate about empowering every person and organization on the planet.",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        "follower_count": 3200000,
        "is_monitoring_active": 1
    },
    {
        "username": "sundarpichai",
        "display_name": "Sundar Pichai",
        "email": "sundar@google.internal",
        "bio": "CEO of Alphabet and Google. Developing technology that helps everyone, everywhere.",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
        "follower_count": 5400000,
        "is_monitoring_active": 1
    },
    {
        "username": "vitalikbuterin",
        "display_name": "Vitalik Buterin",
        "email": "vitalik@ethereum.org.internal",
        "bio": "Ethereum co-founder. Decentralization, cryptography, and open source systems.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "follower_count": 5100000,
        "is_monitoring_active": 1
    },
    {
        "username": "taylorswift",
        "display_name": "Taylor Swift",
        "email": "taylor@swiftmgmt.internal",
        "bio": "Musician, songwriter, director. The Eras Tour. All's fair in love and poetry.",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "follower_count": 280000000,
        "is_monitoring_active": 1
    }
]

DEMO_SEED_PROFILES = [
    # 1. Official/Authentic Demo Profiles
    {
        "username": "elonmusk",
        "display_name": "Elon Musk",
        "bio": "CEO of Tesla, SpaceX, xAI & CTO of X. Exploring the universe and accelerating sustainable energy.",
        "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&auto=format&fit=crop&q=80",
        "followers_count": 180500000,
        "following_count": 640,
        "posts_count": 42100,
        "account_age_days": 5400,
        "is_verified": 1
    },
    # 2. Critical Risk Impersonator & Phishing Giveaway Clone
    {
        "username": "elonmusk_official",
        "display_name": "Elon Musk",
        "bio": "CEO of Tesla & X. Special Crypto Giveaway happening now! Click link below or DM for promo. Free Bitcoin & ETH distribution.",
        "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&auto=format&fit=crop&q=80",
        "followers_count": 14,
        "following_count": 1820,
        "posts_count": 2,
        "account_age_days": 2,
        "is_verified": 0
    },
    # 3. High Risk Typosquat
    {
        "username": "elon_muskk",
        "display_name": "Elon Musk",
        "bio": "CEO of Tesla, SpaceX, xAI & CTO of X. Official backup account.",
        "avatar_url": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150&auto=format&fit=crop&q=80",
        "followers_count": 45,
        "following_count": 890,
        "posts_count": 0,
        "account_age_days": 5,
        "is_verified": 0
    },
    # 4. Critical Risk Phishing Support Clone for Satya Nadella
    {
        "username": "satya_nadella_support",
        "display_name": "Satya Nadella Official Helpdesk",
        "bio": "Microsoft executive help desk. WhatsApp only +1-555-0199 for account recovery and support desk DM.",
        "avatar_url": "",
        "followers_count": 2,
        "following_count": 940,
        "posts_count": 0,
        "account_age_days": 1,
        "is_verified": 0
    },
    # 5. Mass-Following Spam Bot (Not targeting a person, but classic fake bot profile)
    {
        "username": "crypto_profit_bot99",
        "display_name": "Guaranteed Crypto Wealth",
        "bio": "Guaranteed returns daily! Free bitcoin and airdrop rewards. Join our Telegram channel.",
        "avatar_url": "",
        "followers_count": 8,
        "following_count": 4820,
        "posts_count": 1,
        "account_age_days": 12,
        "is_verified": 0
    },
    # 6. Benign everyday developer
    {
        "username": "alex_tech_dev",
        "display_name": "Alex Chen",
        "bio": "Full-stack engineer building AI interfaces and open source tools. Coffee enthusiast ☕",
        "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
        "followers_count": 1420,
        "following_count": 390,
        "posts_count": 156,
        "account_age_days": 820,
        "is_verified": 0
    },
    # 7. Benign photographer
    {
        "username": "sarah_photographer",
        "display_name": "Sarah Miller",
        "bio": "Landscape & street photographer based in Seattle. Prints available upon request 📷",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80",
        "followers_count": 3800,
        "following_count": 620,
        "posts_count": 410,
        "account_age_days": 1100,
        "is_verified": 0
    },
    # 8. Subtle lookalike for Sundar Pichai
    {
        "username": "sundarpichai_fan",
        "display_name": "Sundar Pichai Fanclub",
        "bio": "Fan community celebrating Google AI announcements and CEO keynote updates. Not affiliated with Google.",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
        "followers_count": 850,
        "following_count": 120,
        "posts_count": 88,
        "account_age_days": 340,
        "is_verified": 0
    }
]

def seed_database_if_empty():
    """Seeds protected profiles and demo platform accounts if database is fresh."""
    existing_protected = query_db("SELECT COUNT(*) as count FROM protected_profiles", one=True)
    if existing_protected and existing_protected["count"] == 0:
        conn = get_db()
        cur = conn.cursor()
        for p in PROTECTED_SEED_PROFILES:
            cur.execute("""
                INSERT INTO protected_profiles (username, display_name, email, bio, avatar_url, follower_count, is_monitoring_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (p["username"], p["display_name"], p["email"], p["bio"], p["avatar_url"], p["follower_count"], p["is_monitoring_active"]))

        for d in DEMO_SEED_PROFILES:
            cur.execute("""
                INSERT INTO demo_profiles (username, display_name, bio, avatar_url, followers_count, following_count, posts_count, account_age_days, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (d["username"], d["display_name"], d["bio"], d["avatar_url"], d["followers_count"], d["following_count"], d["posts_count"], d["account_age_days"], d["is_verified"]))

        conn.commit()
        conn.close()
        print("[DATABASE] Seeded initial protected and demo sandbox profiles.")
