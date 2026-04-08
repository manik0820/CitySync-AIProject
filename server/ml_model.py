"""
ml_model.py
-----------
Loads the trained XGBoost model and exposes one function:

    get_priority_score(severity_label, urgency_score, category,
                       recurrence_count, population_density,
                       days_since_filed, estimated_cost)
    → returns float priority score in [0, 100]

Called by main.py every time a new complaint is submitted.
"""

import pickle
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Load model artifacts at module startup (once, not on every request)
# ---------------------------------------------------------------------------

with open("model/priority_model.pkl", "rb") as f:
    _model = pickle.load(f)

with open("model/scaler.pkl", "rb") as f:
    _scaler = pickle.load(f)

with open("model/label_encoders.pkl", "rb") as f:
    _encoders = pickle.load(f)

_le_category = _encoders["category"]
_le_severity = _encoders["severity"]

# ---------------------------------------------------------------------------
# Safe label encoding
# Handles unseen categories/severities gracefully instead of crashing
# ---------------------------------------------------------------------------

def _encode_category(category: str) -> int:
    category = category.lower().strip()
    if category in _le_category.classes_:
        return int(_le_category.transform([category])[0])
    return int(_le_category.transform(["other"])[0])   # fallback


def _encode_severity(severity: str) -> int:
    severity = severity.strip().capitalize()
    if severity in _le_severity.classes_:
        return int(_le_severity.transform([severity])[0])
    return int(_le_severity.transform(["Low"])[0])     # fallback


# ---------------------------------------------------------------------------
# Main function — called by main.py
# ---------------------------------------------------------------------------

def get_priority_score(
    severity_label:     str,
    urgency_score:      float,
    category:           str,
    recurrence_count:   int   = 1,
    population_density: float = 1000.0,
    days_since_filed:   float = 0.0,
    estimated_cost:     float = 5000.0,
) -> float:
    """
    Takes complaint features and returns a priority score in [0, 100].

    Parameters
    ----------
    severity_label     : "Critical" | "High" | "Medium" | "Low"
    urgency_score      : float from nlp_module, range [0.0, 1.0]
    category           : e.g. "road", "water", "sanitation", "lighting",
                         "public_safety", "other"
    recurrence_count   : how many times this area has had similar complaints
    population_density : people per sq km in the complaint area (default 1000)
    days_since_filed   : how many days since the complaint was filed (0 = now)
    estimated_cost     : estimated resolution cost in rupees (default 5000)

    Returns
    -------
    float : priority score rounded to 2 decimal places, clamped to [0, 100]
    """

    # Encode categoricals
    category_enc = _encode_category(category)
    severity_enc = _encode_severity(severity_label)

    # Build feature vector — must match FEATURES order in train_model.py
    features = np.array([[
        category_enc,
        severity_enc,
        float(urgency_score),
        float(recurrence_count),
        float(population_density),
        float(days_since_filed),
        float(estimated_cost),
    ]])

    # Scale using the same scaler fitted during training
    features_scaled = _scaler.transform(features)

    # Predict
    raw_score = float(_model.predict(features_scaled)[0])

    # After getting raw ML score
    impact_weight = min((population_density / 5000) * 10, 10)
    alpha = 0.5
    P_final = (raw_score * impact_weight) / (estimated_cost ** alpha)
    return round(max(0.0, min(100.0, P_final)), 2)

# ---------------------------------------------------------------------------
# Quick test — run this file directly to verify the model loads correctly
# python ml_model.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        {
            "label": "Critical road complaint, high urgency",
            "args": {
                "severity_label":     "Critical",
                "urgency_score":      0.95,
                "category":           "road",
                "recurrence_count":   8,
                "population_density": 4000,
                "days_since_filed":   0,
                "estimated_cost":     8000,
            }
        },
        {
            "label": "High severity water complaint",
            "args": {
                "severity_label":     "High",
                "urgency_score":      0.65,
                "category":           "water",
                "recurrence_count":   3,
                "population_density": 2000,
                "days_since_filed":   2,
                "estimated_cost":     15000,
            }
        },
        {
            "label": "Low severity aesthetic complaint",
            "args": {
                "severity_label":     "Low",
                "urgency_score":      0.10,
                "category":           "other",
                "recurrence_count":   1,
                "population_density": 500,
                "days_since_filed":   10,
                "estimated_cost":     2000,
            }
        },
    ]

    print("=== ML Model Test ===\n")
    for case in test_cases:
        score = get_priority_score(**case["args"])
        print(f"Case    : {case['label']}")
        print(f"Score   : {score} / 100\n")