"""
train_model.py
--------------
Run this file ONCE to train the XGBoost priority scoring model and save it.

Usage:
    python train_model.py

Output:
    model/priority_model.pkl   ← the trained model
    model/scaler.pkl           ← the feature scaler
"""

import os
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# ---------------------------------------------------------------------------
# Step 1 — Generate synthetic training data
# ---------------------------------------------------------------------------
# We don't have real municipal data, so we generate realistic synthetic rows.
# Each row represents one complaint with its features and a ground-truth
# priority score (0–100) assigned using a realistic formula.
# ---------------------------------------------------------------------------

np.random.seed(42)
N = 200  # number of synthetic complaints

CATEGORIES    = ["road", "water", "sanitation", "lighting", "public_safety", "other"]
SEVERITIES    = ["Critical", "High", "Medium", "Low"]
STATUSES      = ["pending"]

# Random feature generation
category       = np.random.choice(CATEGORIES, N)
severity       = np.random.choice(SEVERITIES, N, p=[0.15, 0.30, 0.35, 0.20])
urgency_score  = np.where(
    severity == "Critical", np.random.uniform(0.75, 1.00, N),
    np.where(severity == "High", np.random.uniform(0.50, 0.75, N),
    np.where(severity == "Medium", np.random.uniform(0.25, 0.50, N),
             np.random.uniform(0.05, 0.25, N)))
)
recurrence_count   = np.random.randint(1, 15, N)
population_density = np.random.uniform(100, 5000, N)   # people per sq km
days_since_filed   = np.random.uniform(0, 30, N)
estimated_cost     = np.random.uniform(500, 50000, N)  # in rupees

# ---------------------------------------------------------------------------
# Step 2 — Compute ground-truth priority score
# ---------------------------------------------------------------------------
# This formula encodes the "priority-per-cost" principle from the paper.
# A real system would have officer-annotated labels — this is the best
# approximation for a synthetic dataset.
# ---------------------------------------------------------------------------

SEVERITY_SCORE = {"Critical": 40, "High": 30, "Medium": 20, "Low": 10}
severity_num   = np.array([SEVERITY_SCORE[s] for s in severity])

CATEGORY_BONUS = {
    "public_safety": 10,
    "water":          8,
    "sanitation":     6,
    "road":           5,
    "lighting":       3,
    "other":          0,
}
category_bonus = np.array([CATEGORY_BONUS[c] for c in category])

# Core formula:
#   severity weight (40 max)
# + urgency contribution (25 max)
# + recurrence (10 max)
# + population density (10 max)
# + time pressure (5 max)
# + category bonus (10 max)
# - cost dampening (small penalty for very expensive jobs)
# = raw score, clamped to [0, 100]

raw_priority = (
    severity_num
    + urgency_score * 25
    + np.clip(recurrence_count / 15 * 10, 0, 10)
    + np.clip(population_density / 5000 * 10, 0, 10)
    + np.clip((30 - days_since_filed) / 30 * 5, 0, 5)
    + category_bonus
    - np.log1p(estimated_cost / 10000) * 2   # mild cost dampening
    + np.random.normal(0, 2, N)              # small noise for realism
)

priority_score = np.clip(raw_priority, 0, 100).round(2)

# ---------------------------------------------------------------------------
# Step 3 — Build DataFrame
# ---------------------------------------------------------------------------

df = pd.DataFrame({
    "category":           category,
    "severity_label":     severity,
    "urgency_score":      urgency_score.round(4),
    "recurrence_count":   recurrence_count,
    "population_density": population_density.round(2),
    "days_since_filed":   days_since_filed.round(2),
    "estimated_cost":     estimated_cost.round(2),
    "priority_score":     priority_score,
})

print("=== Synthetic Training Data ===")
print(df.head(10).to_string(index=False))
print(f"\nTotal rows: {len(df)}")
print(f"Priority score range: {df['priority_score'].min():.1f} – {df['priority_score'].max():.1f}")
print(f"Mean priority score:  {df['priority_score'].mean():.1f}")

# ---------------------------------------------------------------------------
# Step 4 — Encode categorical features
# ---------------------------------------------------------------------------

le_category = LabelEncoder()
le_severity = LabelEncoder()

df["category_enc"] = le_category.fit_transform(df["category"])
df["severity_enc"] = le_severity.fit_transform(df["severity_label"])

FEATURES = [
    "category_enc",
    "severity_enc",
    "urgency_score",
    "recurrence_count",
    "population_density",
    "days_since_filed",
    "estimated_cost",
]

X = df[FEATURES]
y = df["priority_score"]

# ---------------------------------------------------------------------------
# Step 5 — Scale features
# ---------------------------------------------------------------------------

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------------------------------------------------------------------------
# Step 6 — Train / test split and model training
# ---------------------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

model = XGBRegressor(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=0,
)

model.fit(X_train, y_train)

# ---------------------------------------------------------------------------
# Step 7 — Evaluate
# ---------------------------------------------------------------------------

y_pred = model.predict(X_test)
mae    = mean_absolute_error(y_test, y_pred)
r2     = r2_score(y_test, y_pred)

print(f"\n=== Model Evaluation ===")
print(f"Mean Absolute Error : {mae:.2f} points (out of 100)")
print(f"R² Score            : {r2:.4f}")
print(f"\nSample predictions vs actual:")
for actual, predicted in zip(y_test[:8], y_pred[:8]):
    print(f"  Actual: {actual:.1f}   Predicted: {predicted:.1f}")

# ---------------------------------------------------------------------------
# Step 8 — Save model, scaler, and encoders
# ---------------------------------------------------------------------------

os.makedirs("model", exist_ok=True)

with open("model/priority_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("model/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

with open("model/label_encoders.pkl", "wb") as f:
    pickle.dump({"category": le_category, "severity": le_severity}, f)

print("\n=== Saved ===")
print("  model/priority_model.pkl")
print("  model/scaler.pkl")
print("  model/label_encoders.pkl")
print("\nDone. Run ml_model.py next to verify the model loads correctly.")