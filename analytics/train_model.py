"""
Fuel Demand Prediction Model — Training Pipeline
=================================================
Trains a Gradient Boosting regressor to predict daily fuel demand
(litres) per station, fuel type, and date.

Run:
    python analytics/setup_ml.py          # first time — installs deps
    python analytics/train_model.py       # trains and saves model

Outputs:
    analytics/model/demand_model.pkl      — trained model
    analytics/model/feature_columns.pkl   — ordered feature list
    analytics/model/training_report.txt   — evaluation metrics
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "fuel_demand_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
os.makedirs(MODEL_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("Loading dataset ...")
df = pd.read_csv(DATA_FILE, parse_dates=["date"])
print(f"  Rows     : {len(df):,}")
print(f"  Columns  : {list(df.columns)}")


# ---------------------------------------------------------------------------
# 2. Feature engineering
# ---------------------------------------------------------------------------
print("\nEngineering features ...")

# Cyclical encoding for periodic features (captures wrap-around)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["dow_sin"]   = np.sin(2 * np.pi * df["day_of_week_num"] / 7)
df["dow_cos"]   = np.cos(2 * np.pi * df["day_of_week_num"] / 7)
df["week_sin"]  = np.sin(2 * np.pi * df["week_of_year"] / 52)
df["week_cos"]  = np.cos(2 * np.pi * df["week_of_year"] / 52)
df["day_sin"]   = np.sin(2 * np.pi * df["day"] / 31)
df["day_cos"]   = np.cos(2 * np.pi * df["day"] / 31)

# Year as numeric trend
df["year_num"] = df["year"] - 2021

# Encode categorical: station_id, fuel_type
le_fuel = LabelEncoder()
df["fuel_type_enc"] = le_fuel.fit_transform(df["fuel_type"])

# Station stays numeric (ID)
# Price normalised per fuel type (z-score within group)
df["price_z"] = df.groupby("fuel_type")["price_per_litre"].transform(
    lambda x: (x - x.mean()) / x.std()
)

# Demand lag features (7-day and 30-day rolling averages per station+fuel)
df = df.sort_values(["station_id", "fuel_type_enc", "date"]).reset_index(drop=True)
df["demand_lag7"]  = df.groupby(["station_id", "fuel_type_enc"])["demand_litres"].transform(
    lambda x: x.shift(1).rolling(window=7, min_periods=1).mean()
)
df["demand_lag30"] = df.groupby(["station_id", "fuel_type_enc"])["demand_litres"].transform(
    lambda x: x.shift(1).rolling(window=30, min_periods=1).mean()
)

# Drop first 30 rows per group (lag warmup) — keep clean data
df = df.dropna(subset=["demand_lag7", "demand_lag30"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "station_id",
    "fuel_type_enc",
    "year_num",
    "month",
    "day",
    "day_of_week_num",
    "is_weekend",
    "is_holiday",
    "price_per_litre",
    "price_z",
    "quarter",
    "week_of_year",
    "seasonal_factor",
    "month_sin", "month_cos",
    "dow_sin",   "dow_cos",
    "week_sin",  "week_cos",
    "day_sin",   "day_cos",
    "demand_lag7",
    "demand_lag30",
]

TARGET = "demand_litres"

X = df[FEATURE_COLS].values
y = df[TARGET].values

print(f"  Feature matrix : {X.shape}")
print(f"  Target vector  : {y.shape}")


# ---------------------------------------------------------------------------
# 3. Train / test split (last 20% as test — temporal split)
# ---------------------------------------------------------------------------
split_idx = int(len(df) * 0.80)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"\n  Train rows     : {len(X_train):,}")
print(f"  Test  rows     : {len(X_test):,}")


# ---------------------------------------------------------------------------
# 4. Train model
# ---------------------------------------------------------------------------
print("\nTraining Gradient Boosting Regressor ...")
model = GradientBoostingRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    min_samples_leaf=10,
    random_state=42,
    verbose=0,
)
model.fit(X_train, y_train)
print("  Training complete.")


# ---------------------------------------------------------------------------
# 5. Evaluate
# ---------------------------------------------------------------------------
y_pred = model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2   = r2_score(y_test, y_pred)
mape = np.mean(np.abs((y_test - y_pred) / np.maximum(y_test, 1))) * 100

print("\n" + "=" * 50)
print("  MODEL EVALUATION (Test Set)")
print("=" * 50)
print(f"  MAE   : {mae:,.1f} litres")
print(f"  RMSE  : {rmse:,.1f} litres")
print(f"  R²    : {r2:.4f}")
print(f"  MAPE  : {mape:.2f}%")
print("=" * 50)

# Feature importance
importances = model.feature_importances_
feat_imp = sorted(zip(FEATURE_COLS, importances), key=lambda x: -x[1])
print("\n  Top 10 Features:")
for name, imp in feat_imp[:10]:
    print(f"    {name:20s} {imp:.4f}")


# ---------------------------------------------------------------------------
# 6. Save artefacts
# ---------------------------------------------------------------------------
model_path    = os.path.join(MODEL_DIR, "demand_model.pkl")
columns_path  = os.path.join(MODEL_DIR, "feature_columns.pkl")
encoders_path = os.path.join(MODEL_DIR, "label_encoders.pkl")
report_path   = os.path.join(MODEL_DIR, "training_report.txt")

joblib.dump(model, model_path)
joblib.dump(FEATURE_COLS, columns_path)
joblib.dump({"fuel_type": le_fuel}, encoders_path)

report = f"""
Fuel Demand Prediction — Training Report
=========================================
Date range  : 2021-01-01 to 2024-12-31
Stations    : 6
Fuel types  : 3 (Petrol, Diesel, Kerosene)
Total rows  : {len(df):,}

Model       : GradientBoostingRegressor
Estimators  : 500
Max depth   : 6
Learning r. : 0.05

Train rows  : {len(X_train):,}
Test  rows  : {len(X_test):,}

MAE   : {mae:,.1f} litres
RMSE  : {rmse:,.1f} litres
R²    : {r2:.4f}
MAPE  : {mape:.2f}%

Top Features:
{chr(10).join(f"  {n:20s} {imp:.4f}" for n, imp in feat_imp[:10])}
"""

with open(report_path, "w") as f:
    f.write(report)

print(f"\nSaved:")
print(f"  Model        : {model_path}")
print(f"  Features     : {columns_path}")
print(f"  Encoders     : {encoders_path}")
print(f"  Report       : {report_path}")
print("\nDone.")
