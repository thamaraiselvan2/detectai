import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATABASE_PATH = os.path.join(BASE_DIR, "fakedetector.db")

# Support starting Flask from either the repository root or backend directory.
for _env_path in (os.path.join(PROJECT_DIR, ".env"), os.path.join(BASE_DIR, ".env")):
    if os.path.isfile(_env_path):
        load_dotenv(_env_path, override=False)

# Risk Level Classification Thresholds
RISK_LEVELS = {
    "LOW": (0, 29),
    "MEDIUM": (30, 59),
    "HIGH": (60, 79),
    "CRITICAL": (80, 100)
}

# Impersonation Alert Threshold: Minimum score to raise an automated alert
MONITORING_ALERT_THRESHOLD = 50

# Similarity metric thresholds
USERNAME_SIMILARITY_HIGH = 0.85
USERNAME_SIMILARITY_MODERATE = 0.70
DISPLAY_NAME_SIMILARITY_HIGH = 0.88

# Email simulation settings
EMAIL_CONFIG = {
    "ENABLED": True,
    "SENDER": "security-alerts@fakedetector.system",
    "SIMULATE_ONLY": True
}
