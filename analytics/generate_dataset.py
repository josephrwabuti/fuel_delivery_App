"""
Fuel Demand Dataset Generator for FuelGo Tanzania
==================================================
Generates realistic daily fuel demand records across multiple stations
from January 2021 to December 2024 (48 months / ~1,461 days).

Run:
    python analytics/generate_dataset.py

Output:
    analytics/fuel_demand_dataset.csv
"""

import csv
import os
import random
import math
from datetime import date, timedelta

random.seed(42)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 12, 31)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fuel_demand_dataset.csv")

# 6 stations in Dar es Salaam region (matches accounts.Station fields)
STATIONS = [
    {"id": 1, "name": "FuelGo Kariakoo",      "lat": -6.7830, "lng": 39.2083, "base_demand": 1800},
    {"id": 2, "name": "FuelGo Kinondoni",      "lat": -6.7730, "lng": 39.2140, "base_demand": 1500},
    {"id": 3, "name": "FuelGo Temeke",         "lat": -6.8500, "lng": 39.2800, "base_demand": 1200},
    {"id": 4, "name": "FuelGo Ubungo",         "lat": -6.7700, "lng": 39.2300, "base_demand": 1100},
    {"id": 5, "name": "FuelGo Ilala",          "lat": -6.8100, "lng": 39.2600, "base_demand": 1400},
    {"id": 6, "name": "FuelGo Sinza",          "lat": -6.7600, "lng": 39.2200, "base_demand": 1000},
]

# Fuel types with realistic Tanzanian price ranges (TZS per litre, 2021 baseline)
FUEL_TYPES = {
    "Petrol":   {"base_price": 2500, "demand_share": 0.45, "volatility": 0.08},
    "Diesel":   {"base_price": 2400, "demand_share": 0.38, "volatility": 0.07},
    "Kerosene": {"base_price": 2000, "demand_share": 0.17, "volatility": 0.06},
}

# Tanzanian public holidays (month, day)
HOLIDAYS = [
    (1, 1),   # New Year's Day
    (1, 12),  # Zanzibar Revolution Day
    (2, 16),  # Union Day
    (3, 26),  # Muungano Day
    (4, 7),   # Karume Day
    (4, 26),  # Union Day (actually Apr 26)
    (5, 1),   # Labour Day
    (5, 25),  # Africa Day
    (7, 7),   # Saba Saba
    (8, 8),   # Nane Nane
    (10, 14), # Mwalimu Nyerere Day
    (12, 9),  # Independence Day
    (12, 25), # Christmas
    (12, 26), # Boxing Day
]

# Islamic holidays shift each year (approximate lunar calendar dates)
# We model Eid al-Fitr and Eid al-Adha as movable holidays
EID_AL_FITR_MONTHS = {
    2021: (5, 13), 2022: (5, 2), 2023: (4, 21), 2024: (4, 10),
}
EID_AL_ADHA_MONTHS = {
    2021: (7, 20), 2022: (7, 9), 2023: (6, 28), 2024: (6, 17),
}


def is_holiday(d):
    """Check if a date is a public holiday."""
    if (d.month, d.day) in HOLIDAYS:
        return True
    year = d.year
    if year in EID_AL_FITR_MONTHS:
        em = EID_AL_FITR_MONTHS[year]
        if d.month == em[0] and d.day == em[1]:
            return True
    if year in EID_AL_ADHA_MONTHS:
        em = EID_AL_ADHA_MONTHS[year]
        if d.month == em[0] and d.day == em[1]:
            return True
    return False


def seasonal_factor(d):
    """
    Seasonal demand multiplier for Tanzania.
    - Dry season (Jun-Oct): higher demand
    - Short rains (Oct-Dec): slightly lower
    - Long rains (Mar-May): lower demand
    - Holiday periods (Dec-Jan, Jul): spikes
    """
    month = d.month
    factors = {
        1: 1.15,   # Jan - holiday carryover, dry
        2: 0.95,   # Feb - normal
        3: 0.88,   # Mar - long rains begin
        4: 0.85,   # Apr - peak long rains
        5: 0.90,   # May - rains tapering
        6: 1.05,   # Jun - dry season starts
        7: 1.12,   # Jul - dry + Saba Saba
        8: 1.08,   # Aug - dry + Nane Nane
        9: 1.00,   # Sep - end of dry
        10: 0.95,  # Oct - short rains begin
        11: 0.92,  # Nov - short rains
        12: 1.18,  # Dec - year-end rush + holidays
    }
    return factors[month]


def price_trend(base_price, d, volatility):
    """
    Simulate realistic fuel price movement.
    Gradual upward trend with monthly fluctuations reflecting
    global oil price changes and TZS exchange rate movements.
    """
    # Months since start
    months_elapsed = (d.year - START_DATE.year) * 12 + (d.month - START_DATE.month)
    # ~8-12% annual increase (Tanzanian fuel price trend)
    annual_increase = 0.10
    trend = base_price * (1 + annual_increase * months_elapsed / 12)
    # Monthly noise
    noise = random.gauss(0, base_price * volatility)
    # Occasional price shocks (supply disruptions)
    if random.random() < 0.02:
        shock = random.choice([-1, 1]) * base_price * random.uniform(0.05, 0.15)
    else:
        shock = 0
    return round(max(trend + noise + shock, base_price * 0.8), 0)


def day_of_week_multiplier(d):
    """Weekly demand pattern — weekdays higher, Saturday moderate, Sunday lowest."""
    dow = d.weekday()
    multipliers = [1.0, 1.02, 1.03, 1.01, 1.05, 0.88, 0.75]
    return multipliers[dow]


def compute_demand(station, fuel_info, d, price):
    """
    Compute daily demand in litres for a given station, fuel type, and date.
    Uses base demand, fuel share, seasonal/weekly/holiday/price adjustments,
    growth trend, and random noise.
    """
    base = station["base_demand"] * fuel_info["demand_share"]

    # Growth trend: ~3-5% annual increase in demand
    years_elapsed = (d - START_DATE).days / 365.25
    growth = 1 + 0.04 * years_elapsed

    seasonal = seasonal_factor(d)
    weekly = day_of_week_multiplier(d)

    # Holiday boost
    holiday = 1.25 if is_holiday(d) else 1.0

    # Day before/after holiday also elevated
    prev_day = d - timedelta(days=1)
    next_day = d + timedelta(days=1)
    if is_holiday(prev_day) or is_holiday(next_day):
        holiday = max(holiday, 1.12)

    # Price sensitivity: higher price → slightly lower demand
    price_factor = fuel_info["base_price"] / price

    # Random daily noise (±20%)
    noise = random.gauss(1.0, 0.10)

    demand = base * growth * seasonal * weekly * holiday * price_factor * noise

    # Ensure minimum demand
    return max(round(demand), 10)


def generate_dataset():
    """Generate the full CSV dataset."""
    rows = []
    current_date = START_DATE
    day_count = 0

    while current_date <= END_DATE:
        for station in STATIONS:
            for fuel_name, fuel_info in FUEL_TYPES.items():
                price = price_trend(fuel_info["base_price"], current_date, fuel_info["volatility"])
                demand = compute_demand(station, fuel_info, current_date, price)

                # Additional per-record features for ML
                row = {
                    "date": current_date.isoformat(),
                    "year": current_date.year,
                    "month": current_date.month,
                    "day": current_date.day,
                    "day_of_week": current_date.strftime("%A"),
                    "day_of_week_num": current_date.weekday(),
                    "is_weekend": 1 if current_date.weekday() >= 5 else 0,
                    "is_holiday": 1 if is_holiday(current_date) else 0,
                    "station_id": station["id"],
                    "station_name": station["name"],
                    "station_lat": station["lat"],
                    "station_lng": station["lng"],
                    "fuel_type": fuel_name,
                    "price_per_litre": price,
                    "demand_litres": demand,
                    "seasonal_factor": round(seasonal_factor(current_date), 3),
                    "quarter": (current_date.month - 1) // 3 + 1,
                    "week_of_year": current_date.isocalendar()[1],
                    "month_name": current_date.strftime("%B"),
                }
                rows.append(row)
        day_count += 1
        current_date += timedelta(days=1)

    # Write CSV
    fieldnames = list(rows[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    total_records = len(rows)
    total_litres = sum(r["demand_litres"] for r in rows)
    unique_dates = len(set(r["date"] for r in rows))

    print(f"Dataset generated: {OUTPUT_FILE}")
    print(f"  Date range     : {START_DATE} to {END_DATE}")
    print(f"  Total days     : {unique_dates}")
    print(f"  Stations       : {len(STATIONS)}")
    print(f"  Fuel types     : {len(FUEL_TYPES)}")
    print(f"  Total records  : {total_records:,}")
    print(f"  Total demand   : {total_litres:,.0f} litres")
    print(f"  Avg daily/stn  : {total_litres / unique_dates / len(STATIONS):,.0f} litres")


if __name__ == "__main__":
    generate_dataset()
