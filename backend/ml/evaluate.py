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

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_store")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "eval_metrics.json")


def evaluate():
    try:
        from sklearn.metrics import (
            precision_score, recall_score, f1_score,
            roc_auc_score, confusion_matrix, classification_report
        )
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("[EVAL] ERROR: scikit-learn not installed. Run: pip install scikit-learn")
        return

    if not os.path.exists(MODEL_PATH):
        print(f"[EVAL] No trained model found at {MODEL_PATH}")
        print("  Run: python backend/ml/train.py first")
        return

    print("[EVAL] Loading model and dataset...")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    from ml.dataset_loader import load_dataset
    X, y, metadata = load_dataset()

    if len(X) < 6:
        print("[EVAL] Not enough samples for evaluation.")
        return

    # Reproduce same split as training
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    if not X_test:
        print("[EVAL] Test split is empty — dataset too small.")
        return

    y_pred = model.predict(X_test)
    y_prob = None
    try:
        y_prob = model.predict_proba(X_test)[:, 1]
    except AttributeError:
        pass

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall    = recall_score(y_test, y_pred, zero_division=0)
    f1        = f1_score(y_test, y_pred, zero_division=0)
    cm        = confusion_matrix(y_test, y_pred).tolist()
    roc_auc   = float(roc_auc_score(y_test, y_prob)) if y_prob is not None and len(set(y_test)) > 1 else None

    metrics = {
        "n_test_samples": len(X_test),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else "N/A (single class in test set)",
        "confusion_matrix": cm,
        "class_distribution_test": {
            "genuine": int(sum(1 for l in y_test if l == 0)),
            "fake": int(sum(1 for l in y_test if l == 1))
        }
    }

    print("\n" + "="*50)
    print("  FAKE PROFILE DETECTOR — MODEL EVALUATION")
    print("="*50)
    print(f"  Test samples : {metrics['n_test_samples']}")
    print(f"  Precision    : {metrics['precision']:.4f}")
    print(f"  Recall       : {metrics['recall']:.4f}")
    print(f"  F1-Score     : {metrics['f1_score']:.4f}")
    print(f"  ROC-AUC      : {metrics['roc_auc']}")
    print(f"\n  Confusion Matrix (rows=actual, cols=predicted):")
    print(f"    TN={cm[0][0]}  FP={cm[0][1]}")
    print(f"    FN={cm[1][0]}  TP={cm[1][1]}")
    print("\n  Full Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Genuine", "Fake"]))

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n  Metrics saved → {METRICS_PATH}")

    return metrics


if __name__ == "__main__":
    evaluate()
