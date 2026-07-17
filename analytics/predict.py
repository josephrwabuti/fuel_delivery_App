"""
Fuel Demand Prediction Utility
===============================
Loads the trained model and generates 7-day demand forecasts
for a provider's station, broken down by fuel type.

Used by the provider_demand view.
"""

import os
import numpy as np
import joblib
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

# Tanzanian public holidays (month, day)
_HOLIDAYS = {
    (1, 1), (1, 12), (2, 16), (3, 26), (4, 7), (4, 26),
    (5, 1), (5, 25), (7, 7), (8, 8), (10, 14), (12, 9),
    (12, 25), (12, 26),
}
_EID_FITR = {(5, 13), (5, 2), (4, 21), (4, 10)}
_EID_ADHA = {(7, 20), (7, 9), (6, 28), (6, 17)}

_SEASONAL = {
    1: 1.15, 2: 0.95, 3: 0.88, 4: 0.85, 5: 0.90, 6: 1.05,
    7: 1.12, 8: 1.08, 9: 1.00, 10: 0.95, 11: 0.92, 12: 1.18,
}

_FUEL_ORDER = ["Petrol", "Diesel", "Kerosene"]

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _is_holiday(d):
    if (d.month, d.day) in _HOLIDAYS:
        return True
    if d.year == 2021 and (d.month, d.day) in _EID_FITR | _EID_ADHA:
        return True
    return False


def _load_model():
    model_path = os.path.join(MODEL_DIR, "demand_model.pkl")
    cols_path = os.path.join(MODEL_DIR, "feature_columns.pkl")
    enc_path = os.path.join(MODEL_DIR, "label_encoders.pkl")
    if not all(os.path.exists(p) for p in [model_path, cols_path, enc_path]):
        return None, None, None
    return (
        joblib.load(model_path),
        joblib.load(cols_path),
        joblib.load(enc_path),
    )


def _build_features(target_date, station_id, fuel_type_enc, price, lag7, lag30):
    """Build the feature vector for one prediction row."""
    import math
    m = target_date.month
    d = target_date.day
    dow = target_date.weekday()
    week = target_date.isocalendar()[1]
    quarter = (m - 1) // 3 + 1

    return [
        station_id,           # station_id
        fuel_type_enc,        # fuel_type_enc
        target_date.year - 2021,  # year_num
        m,                    # month
        d,                    # day
        dow,                  # day_of_week_num
        1 if dow >= 5 else 0,  # is_weekend
        1 if _is_holiday(target_date) else 0,  # is_holiday
        price,                # price_per_litre
        0,                    # price_z (placeholder, filled below)
        quarter,              # quarter
        week,                 # week_of_year
        _SEASONAL.get(m, 1.0),  # seasonal_factor
        math.sin(2 * math.pi * m / 12),   # month_sin
        math.cos(2 * math.pi * m / 12),   # month_cos
        math.sin(2 * math.pi * dow / 7),  # dow_sin
        math.cos(2 * math.pi * dow / 7),  # dow_cos
        math.sin(2 * math.pi * week / 52),  # week_sin
        math.cos(2 * math.pi * week / 52),  # week_cos
        math.sin(2 * math.pi * d / 31),   # day_sin
        math.cos(2 * math.pi * d / 31),   # day_cos
        lag7,                 # demand_lag7
        lag30,                # demand_lag30
    ]


def generate_forecast(station, orders_qs, stock_qs, days_ahead=7):
    """
    Generate a 7-day forecast for a provider's station.

    Args:
        station: accounts.Station instance
        orders_qs: Order queryset filtered to this station
        stock_qs: StationStock queryset filtered to this station
        days_ahead: number of days to forecast

    Returns:
        dict with forecast data, or None if model not available
    """
    model, feature_cols, encoders = _load_model()
    if model is None:
        return None

    today = date.today()

    # --- Map real station to synthetic station_id (1-6) ---
    # Use hash of station id modulo 6 + 1 for consistent mapping
    station_id = (station.id % 6) + 1

    # --- Compute lag features from real order history ---
    from django.db.models import Sum
    from datetime import datetime as dt

    # Last 30 days demand per fuel type
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)

    lag_data = {}
    for ft in _FUEL_ORDER:
        qs = orders_qs.filter(
            fuel_type=ft,
            status="delivered",
            created_at__date__gte=thirty_days_ago,
        )
        total_30 = qs.aggregate(s=Sum("quantity"))["s"] or 0
        total_7 = qs.filter(
            created_at__date__gte=seven_days_ago
        ).aggregate(s=Sum("quantity"))["s"] or 0

        days_30 = min((today - thirty_days_ago).days, 30) or 1
        days_7 = min((today - seven_days_ago).days, 7) or 1
        lag_data[ft] = {
            "lag7": round(float(total_7) / days_7),
            "lag30": round(float(total_30) / days_30),
        }

    # --- Get current prices and stock per fuel type ---
    fuel_info = {}
    for s in stock_qs:
        fuel_info[s.fuel_type] = {
            "price": float(s.price_per_litre),
            "stock": float(s.litres_available),
            "capacity": float(s.capacity),
        }
    for ft in _FUEL_ORDER:
        if ft not in fuel_info:
            fuel_info[ft] = {"price": 2500.0, "stock": 0, "capacity": 5000}

    # --- Encode fuel types ---
    fuel_le = encoders["fuel_type"]
    fuel_enc_map = {}
    for ft in _FUEL_ORDER:
        try:
            fuel_enc_map[ft] = int(fuel_le.transform([ft])[0])
        except Exception:
            fuel_enc_map[ft] = 0

    # --- Predict 7 days ---
    daily_forecast = []
    fuel_totals = {ft: 0 for ft in _FUEL_ORDER}
    day_demands = []

    for i in range(days_ahead):
        target = today + timedelta(days=i)
        day_total = 0
        fuel_day = {}

        for ft in _FUEL_ORDER:
            features = _build_features(
                target_date=target,
                station_id=station_id,
                fuel_type_enc=fuel_enc_map[ft],
                price=fuel_info[ft]["price"],
                lag7=lag_data[ft]["lag7"],
                lag30=lag_data[ft]["lag30"],
            )
            pred = max(int(round(model.predict([features])[0])), 0)
            fuel_day[ft] = pred
            fuel_totals[ft] += pred
            day_total += pred

            # Update lags for next prediction
            lag_data[ft]["lag7"] = (lag_data[ft]["lag7"] * 6 + pred) / 7
            lag_data[ft]["lag30"] = (lag_data[ft]["lag30"] * 29 + pred) / 30

        day_demands.append(day_total)
        daily_forecast.append({
            "date": target,
            "day_name": _DAY_NAMES[target.weekday()],
            "day_short": target.strftime("%a"),
            "is_today": target == today,
            "is_tomorrow": target == today + timedelta(days=1),
            "total_litres": day_total,
            "petrol": fuel_day.get("Petrol", 0),
            "diesel": fuel_day.get("Diesel", 0),
            "kerosene": fuel_day.get("Kerosene", 0),
        })

    # --- Compute bar chart percentages ---
    max_day_val = max(day_demands) if day_demands else 1
    for df in daily_forecast:
        df["bar_pct"] = max(int(round(df["total_litres"] / max_day_val * 100)), 3)

    # --- Insights ---
    max_day = max(daily_forecast, key=lambda x: x["total_litres"])
    avg_demand = np.mean(day_demands) if day_demands else 0

    # Highest demand fuel
    fuel_avg = {ft: fuel_totals[ft] / days_ahead for ft in _FUEL_ORDER}
    top_fuel = max(fuel_avg, key=fuel_avg.get)
    total_avg = sum(fuel_avg.values())
    top_fuel_pct = round(fuel_avg[top_fuel] / max(total_avg, 1) * 100) if total_avg else 0

    # Busiest day of week
    dow_totals = {}
    for df in daily_forecast:
        dn = df["day_name"]
        dow_totals[dn] = dow_totals.get(dn, 0) + df["total_litres"]
    busiest_day = max(dow_totals, key=dow_totals.get) if dow_totals else "N/A"

    # Stock alerts
    stock_alerts = []
    for ft in _FUEL_ORDER:
        info = fuel_info.get(ft, {})
        stock = info.get("stock", 0)
        daily_rate = fuel_avg.get(ft, 100)
        if daily_rate > 0:
            days_left = stock / daily_rate
        else:
            days_left = 999
        if days_left < 7:
            stock_alerts.append({
                "fuel_type": ft,
                "stock_litres": int(stock),
                "daily_rate": int(daily_rate),
                "days_left": round(days_left, 1),
                "urgency": "critical" if days_left < 2 else "warning" if days_left < 5 else "notice",
            })

    # Recommendations
    recommendations = []
    if stock_alerts:
        worst = min(stock_alerts, key=lambda x: x["days_left"])
        need = max(int(worst["daily_rate"] * 7 - worst["stock_litres"]), 1000)
        recommendations.append({
            "icon": "fas fa-gas-pump",
            "color": "red",
            "title": f"Restock {worst['fuel_type']} urgently",
            "detail": f"Only {worst['days_left']} days of stock left. "
                      f"Order at least {need:,}L to cover the next 7 days.",
        })

    if max_day["day_name"] in ("Friday", "Saturday", "Sunday"):
        recommendations.append({
            "icon": "fas fa-id-badge",
            "color": "orange",
            "title": f"Extra drivers on {max_day['day_name']}",
            "detail": f"Predicted {max_day['total_litres']:,}L demand — "
                      f"the busiest day this week. Ensure full driver coverage.",
        })

    spike_days = [d for d in daily_forecast if d["total_litres"] > avg_demand * 1.2]
    if spike_days:
        names = ", ".join(d["day_name"] for d in spike_days[:3])
        pct = int((max(day_demands) / max(avg_demand, 1) - 1) * 100)
        recommendations.append({
            "icon": "fas fa-chart-line",
            "color": "blue",
            "title": f"Demand spikes on {names}",
            "detail": f"Expect up to {pct}% above average. "
                      f"Consider extending operating hours on those days.",
        })

    if not recommendations:
        recommendations.append({
            "icon": "fas fa-check-circle",
            "color": "green",
            "title": "Stock levels look good",
            "detail": "No urgent restocking needed based on this week's forecast.",
        })

    # Alert message
    if spike_days:
        peak_names = " & ".join(d["day_name"] for d in spike_days[:2])
        spike_pct = int((max(day_demands) / max(avg_demand, 1) - 1) * 100)
        alert = {
            "title": f"High demand predicted {peak_names}",
            "detail": f"Orders expected to spike {spike_pct}% above average. "
                      f"Consider restocking and scheduling extra drivers.",
        }
    else:
        alert = {
            "title": "Demand is stable this week",
            "detail": "No major spikes predicted. Maintain current stock levels.",
        }

    return {
        "daily": daily_forecast,
        "max_demand": max(day_demands) if day_demands else 0,
        "peak_day_name": max_day["day_name"],
        "avg_demand": int(avg_demand),
        "top_fuel": top_fuel,
        "top_fuel_pct": top_fuel_pct,
        "busiest_day": busiest_day,
        "stock_alerts": stock_alerts,
        "recommendations": recommendations,
        "alert": alert,
        "fuel_totals": fuel_totals,
        "total_7day": sum(day_demands),
    }
