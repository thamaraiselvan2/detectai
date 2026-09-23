"""
Model training script for fake profile detection.
Trains Logistic Regression (baseline) and Random Forest (main model).
Run this once: python backend/ml/train.py

DO NOT run during API requests — model is loaded once at startup via predictor.py
"""

import sys
import os
import json
import pickle

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ml.dataset_loader import load_dataset
from ml.features import FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_store")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "feature_config.json")
METRICS_PATH = os.path.join(MODEL_DIR, "training_metrics.json")


def train():
    if not SKLEARN_AVAILABLE:
        print("[TRAIN] ERROR: scikit-learn is not installed.")
        print("  Run: pip install scikit-learn")
        return False

    os.makedirs(MODEL_DIR, exist_ok=True)

    print("[TRAIN] Loading dataset...")
    X, y, metadata = load_dataset()

    if len(X) < 6:
        print(f"[TRAIN] Not enough samples ({len(X)}) to train a reliable model.")
        print("  Run the app, create some profiles, and perform some checks first.")
        print("  Then re-run this script.")
        return False

    print(f"[TRAIN] Dataset: {len(X)} samples, {len(FEATURE_NAMES)} features")
    print(f"  Class distribution: {sum(y)} fake / {len(y)-sum(y)} genuine")

    # Stratified train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    # ── Model 1: Logistic Regression baseline ────────────────────────────────
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_score = lr_pipeline.score(X_test, y_test) if X_test else 0
    print(f"[TRAIN] Logistic Regression accuracy (test): {lr_score:.3f}")

    # ── Model 2: Random Forest (main model) ──────────────────────────────────
    rf_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ))
    ])
    rf_pipeline.fit(X_train, y_train)
    rf_score = rf_pipeline.score(X_test, y_test) if X_test else 0
    print(f"[TRAIN] Random Forest accuracy (test):       {rf_score:.3f}")

    # ── Save the better model ─────────────────────────────────────────────────
    best_model = rf_pipeline if rf_score >= lr_score else lr_pipeline
    best_name = "RandomForest" if rf_score >= lr_score else "LogisticRegression"
    print(f"[TRAIN] Saving {best_name} model → {MODEL_PATH}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(best_model, f)

    # ── Save feature config ───────────────────────────────────────────────────
    config = {
        "feature_names": FEATURE_NAMES,
        "model_type": best_name,
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "train_accuracy": round(rf_score if best_name == "RandomForest" else lr_score, 4),
        "class_distribution": {"fake": int(sum(y)), "genuine": int(len(y) - sum(y))}
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[TRAIN] Feature config saved → {CONFIG_PATH}")
    print(f"[TRAIN] Training complete. Model is ready to use via predictor.py")
    return True


if __name__ == "__main__":
    success = train()
    sys.exit(0 if success else 1)
