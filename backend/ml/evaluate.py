"""
Model evaluation script — generates real metrics from actual test data.
Run: python backend/ml/evaluate.py

NEVER hardcodes performance numbers.
All metrics come from the model's predictions on the test split.
"""

import sys
import os
import json
import pickle
import argparse

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_store")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
BASELINE_MODEL_PATH = os.path.join(MODEL_DIR, "logistic_regression.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "eval_metrics.json")


def evaluate(csv_path=None):
    try:
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            roc_auc_score, confusion_matrix, classification_report
        )
    except ImportError:
        print("[EVAL] ERROR: scikit-learn not installed. Run: pip install scikit-learn")
        return

    if not os.path.exists(MODEL_PATH):
        print(f"[EVAL] No trained model found at {MODEL_PATH}")
        print("  Run: python backend/ml/train.py first")
        return

    if not os.path.exists(BASELINE_MODEL_PATH):
        print(f"[EVAL] Baseline model not found at {BASELINE_MODEL_PATH}")
        print("  Run python ml/train.py first to save both models.")
        return

    print("[EVAL] Loading model and dataset...")
    with open(MODEL_PATH, "rb") as f:
        random_forest = pickle.load(f)
    with open(BASELINE_MODEL_PATH, "rb") as f:
        logistic_regression = pickle.load(f)

    from ml.dataset_loader import load_dataset, split_dataset
    try:
        X, y, metadata = load_dataset(csv_path)
        X_train, X_test, y_train, y_test = split_dataset(X, y)
    except ValueError as error:
        print(f"[EVAL] ERROR: {error}")
        return None

    def measure(model):
        y_pred = model.predict(X_test)
        y_prob = None
        try:
            y_prob = model.predict_proba(X_test)[:, 1]
        except (AttributeError, IndexError):
            pass
        cm = confusion_matrix(y_test, y_pred).tolist()
        roc_auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None else None
        return {
            "n_test_samples": len(X_test),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
            "roc_auc": round(roc_auc, 4) if roc_auc is not None else "N/A",
            "confusion_matrix": cm,
            "class_distribution_test": {
                "genuine": int(sum(1 for label in y_test if label == 0)),
                "fake": int(sum(1 for label in y_test if label == 1))
            }
        }

    logistic_metrics = measure(logistic_regression)
    random_forest_metrics = measure(random_forest)
    metrics = {
        "dataset_path": os.path.abspath(csv_path or os.getenv("DETECTAI_ML_DATASET", "")),
        "random_state": 42,
        "test_size": 0.2,
        "models": {
            "LogisticRegression": logistic_metrics,
            "RandomForest": random_forest_metrics,
        },
        # Preserve the existing top-level main-model metric contract.
        **random_forest_metrics,
    }

    print("\n" + "="*50)
    print("  FAKE PROFILE DETECTOR — MODEL EVALUATION")
    print("="*50)
    for model_name, model_metrics in metrics["models"].items():
        cm = model_metrics["confusion_matrix"]
        print(f"\n  {model_name}")
        print(f"    Test samples : {model_metrics['n_test_samples']}")
        print(f"    Precision    : {model_metrics['precision']:.4f}")
        print(f"    Recall       : {model_metrics['recall']:.4f}")
        print(f"    F1-Score     : {model_metrics['f1_score']:.4f}")
        print(f"    ROC-AUC      : {model_metrics['roc_auc']}")
        print(f"    Confusion    : TN={cm[0][0]} FP={cm[0][1]} FN={cm[1][0]} TP={cm[1][1]}")

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Metrics saved → {METRICS_PATH}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the saved model on a labeled CSV test split.")
    parser.add_argument("--dataset", help="Path to the labeled CSV; overrides DETECTAI_ML_DATASET.")
    args = parser.parse_args()
    evaluate(args.dataset)
