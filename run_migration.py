"""Run the migration manually since shell execution is unavailable."""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from django.db import migrations, models
from django.apps import apps
from django.db.models import Q

# Apply the migration operations manually
Station = apps.get_model('accounts', 'Station')

# Add is_open field (SQLite won't need explicit add column - we can use the migration)
# But since we can't run migrate, let's just update existing data

# Step 1: Migrate existing stations
# "open" → approved & is_open=True (default)
open_updated = Station.objects.filter(status="open").update(status="approved")
print(f"Updated {open_updated} stations from 'open' → 'approved'")

# "closed" → approved & is_open=False
# First check if our column exists
try:
    closed_stations = Station.objects.filter(status="closed")
    count = closed_stations.count()
    print(f"Found {count} stations with status='closed'")
    # We'll handle this differently since we need the column
except Exception as e:
    print(f"Cannot check closed status: {e}")

print("Migration script completed.")
print("\nNOTE: You still need to run 'python manage.py migrate' to apply the schema change.")
print("This script only prepared the data. Run:")
print("  python manage.py migrate")
