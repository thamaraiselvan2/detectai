"""
ML model predictor — lazy singleton that loads the trained model once.
Used by the detection pipeline to enrich results with ML probability.

Graceful fallback: if no model is trained yet, predict() returns None.
"""

import os
import pickle
import json

_MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_store")
_MODEL_PATH = os.path.join(_MODEL_DIR, "model.pkl")
_CONFIG_PATH = os.path.join(_MODEL_DIR, "feature_config.json")

_model = None          # lazy loaded
_config = None         # lazy loaded
_load_attempted = False


def _load_model():
    """Loads model and config once. Returns True if successful."""
    global _model, _config, _load_attempted
    if _load_attempted:
        return _model is not None
    _load_attempted = True

    if not os.path.exists(_MODEL_PATH):
        return False

    try:
        with open(_MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        if os.path.exists(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r") as f:
                _config = json.load(f)
        print(f"[ML] Model loaded: {_config.get('model_type', 'unknown') if _config else 'unknown'}")
        return True
    except Exception as e:
        print(f"[ML] Failed to load model: {e}")
        _model = None
        return False


def is_model_available() -> bool:
    """Returns True if a trained model is available."""
    return _load_model()


def get_model_info() -> dict:
    """Returns model config info for API responses."""
    if not _load_model() or _config is None:
        return {
            "available": False,
            "model_type": None,
            "message": "ML unavailable: no trained model artifact is present.",
        }
    return {
        "available": True,
        "model_type": _config.get("model_type"),
        "n_train_samples": _config.get("n_train_samples"),
        "n_test_samples": _config.get("n_test_samples"),
        "test_accuracy": _config.get("test_accuracy"),
        "baseline_model_type": _config.get("baseline_model_type"),
        "baseline_test_accuracy": _config.get("baseline_test_accuracy"),
        "dataset_path": _config.get("dataset_path"),
    }


def predict(feature_vector: list) -> dict | None:
    """
    Predicts whether a profile is fake given its feature vector.

    Returns:
        dict with keys:
          - ml_probability: float 0.0–1.0 (probability of fake)
          - ml_prediction: int 0 or 1
          - ml_model_type: str
        or None if no model is available.
    """
    if not _load_model() or _model is None:
        return {
            "available": False,
            "ml_probability": None,
            "ml_prediction": None,
            "ml_model_type": None,
            "message": "ML unavailable: train a model from a labeled CSV first.",
        }

    try:
        prob = _model.predict_proba([feature_vector])[0][1]
        pred = int(_model.predict([feature_vector])[0])
        return {
            "available": True,
            "ml_probability": round(float(prob), 4),
            "ml_prediction": pred,
            "ml_model_type": _config.get("model_type", "unknown") if _config else "unknown",
        }
    except Exception as e:
        print(f"[ML] Prediction error: {e}")
        return {
            "available": False,
            "ml_probability": None,
            "ml_prediction": None,
            "ml_model_type": None,
            "message": f"ML unavailable: prediction failed ({type(e).__name__}).",
        }
