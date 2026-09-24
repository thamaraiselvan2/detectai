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
import argparse

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ml.dataset_loader import load_dataset, split_dataset
from ml.features import FEATURE_NAMES

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_store")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
BASELINE_MODEL_PATH = os.path.join(MODEL_DIR, "logistic_regression.pkl")
CONFIG_PATH = os.path.join(MODEL_DIR, "feature_config.json")
METRICS_PATH = os.path.join(MODEL_DIR, "training_metrics.json")


def train(csv_path=None):
    if not SKLEARN_AVAILABLE:
        print("[TRAIN] ERROR: scikit-learn is not installed.")
        print("  Run: pip install scikit-learn")
        return False

    print("[TRAIN] Loading dataset...")
    try:
        X, y, metadata = load_dataset(csv_path)
    except ValueError as error:
        print(f"[TRAIN] ERROR: {error}")
        return False

    if len(X) < 10:
        print(f"[TRAIN] Not enough labeled samples ({len(X)}); at least 10 are required.")
        print("  Supply a real labeled CSV and re-run this script.")
        return False

    print(f"[TRAIN] Dataset: {len(X)} samples, {len(FEATURE_NAMES)} features")
    print(f"  Class distribution: {sum(y)} fake / {len(y)-sum(y)} genuine")

    try:
        X_train, X_test, y_train, y_test = split_dataset(X, y)
    except ValueError as error:
        print(f"[TRAIN] ERROR: {error}")
        return False

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

    # Random Forest is the main persisted model; Logistic Regression is the baseline.
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"[TRAIN] Saving RandomForest model → {MODEL_PATH}")

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(rf_pipeline, f)
    with open(BASELINE_MODEL_PATH, "wb") as f:
        pickle.dump(lr_pipeline, f)

    # ── Save feature config ───────────────────────────────────────────────────
    config = {
        "feature_names": FEATURE_NAMES,
        "model_type": "RandomForest",
        "baseline_model_path": BASELINE_MODEL_PATH,
        "model_path": MODEL_PATH,
        "n_train_samples": len(X_train),
        "n_test_samples": len(X_test),
        "baseline_model_type": "LogisticRegression",
        "baseline_test_accuracy": round(lr_score, 4),
        "test_accuracy": round(rf_score, 4),
        "dataset_path": os.path.abspath(csv_path or os.getenv("DETECTAI_ML_DATASET", "")),
        "random_state": 42,
        "test_size": 0.2,
        "class_distribution": {"fake": int(sum(y)), "genuine": int(len(y) - sum(y))}
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[TRAIN] Feature config saved → {CONFIG_PATH}")
    print(f"[TRAIN] Training complete. Model is ready to use via predictor.py")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the fake/bot profile models from a labeled CSV.")
    parser.add_argument("--dataset", help="Path to the labeled CSV; overrides DETECTAI_ML_DATASET.")
    args = parser.parse_args()
    success = train(args.dataset)
    sys.exit(0 if success else 1)
