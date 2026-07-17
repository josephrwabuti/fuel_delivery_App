"""
Setup script — installs required ML libraries.
Run once:  python analytics/setup_ml.py
"""

import subprocess
import sys

REQUIRED = ["pandas", "scikit-learn", "joblib", "numpy"]


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


for pkg in REQUIRED:
    try:
        __import__(pkg)
        print(f"  [OK] {pkg}")
    except ImportError:
        print(f"  [INSTALLING] {pkg} ...")
        install(pkg)

print("\nAll ML dependencies are ready.")
