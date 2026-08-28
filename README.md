# Aegis.Guard • Fake Profile & Impersonation Detection System

A complete web application designed to detect potentially fake, bot, and impersonating social media profiles with an explainable 0–100 risk scoring engine, a controlled demo social network sandbox, protected identity registration, and automated surveillance monitoring.

---

## 🌟 Key Features

1. **Instant Profile Scanner**:
   - Analyzes usernames, follower-to-following ratios, post counts, account age, verification badges, and bio descriptions.
   - Calculates a risk score from **0–100** categorized into **Low (0–29)**, **Medium (30–59)**, **High (60–79)**, and **Critical (80–100)**.
   - Transparent, mathematical factor breakdown explaining *why* the profile received that score.
   - Contextual security recommendation.
   - Side-by-side comparison modal against matched genuine identities.

2. **Protected Identity Vault**:
   - Genuine/original users can register their official username, display name, registered security email, and bio.
   - Instant baseline sweep upon enrollment to detect any active impersonators.
   - Toggleable continuous surveillance monitoring.

3. **Active Surveillance & Alert Center**:
   - Automated threat sweep comparing monitored identities against the demo social platform.
   - Incident alert cards with target vs imposter comparison.
   - Configurable email notification simulation dispatched to the victim's inbox.
   - Threat triage states: `UNREAD`, `ACKNOWLEDGED`, `RESOLVED`.

4. **Demo Social Media Sandbox (SocialSphere)**:
   - Controlled environment to safely simulate social accounts without scraping or external API limits.
   - Pre-configured realistic profiles: authentic leaders, lookalike copycats, fake support desks, and spam bots.
   - Preset attack scenario generator (Elon Giveaway Clone, Satya Helpdesk, Spam Bot).
   - Real-time alert triggers when a clone profile is spawned.

5. **SOC Admin & Threat Intelligence Dashboard**:
   - Telemetry overview: total scans, high-risk flags, active surveillance subscriptions, alert queues.
   - Risk tier distribution charts.
   - Top targeted genuine identity leaderboard.
   - Comprehensive audit log with full factor inspector and environment reset capabilities.

---

## 🛠️ Technology Stack

* **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide React, Axios
* **Backend**: Python 3.13, Flask 3.1, Flask-CORS
* **Database**: SQLite3 (relational schema with full audit history)
* **Detection Engine**: Modular Python risk engine utilizing `difflib.SequenceMatcher`, Levenshtein distance, homoglyph mapping, and behavioral ratio heuristics.

---

## 🚀 Running the Project

### 1. Start the Flask Backend API
```bash
cd backend
pip install -r requirements.txt
python app.py
```
*Backend API will run on `http://localhost:5000`*

### 2. Start the React Frontend
```bash
cd frontend
npm install
npm run dev
```
*Frontend will run on `http://localhost:5173`*

---

## 🧪 Running Unit Tests
```bash
cd backend
python test_engine.py
```
All unit test suites verify benign accounts, blatant clones, typosquats, and spam bot profiles.
