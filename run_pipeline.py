"""
Master Pipeline Runner for Punjab Climate Downscaling & Projection
Executes all processing steps in sequence:
  1. align_era5.py        -> Standardize ERA5 coordinates and physical units
  2. clip_models.py       -> Interpolate and clip CMIP6 models to Punjab
  3. gf_test_and_rank.py  -> Goodness-of-Fit statistical evaluation (MAE, RMSE, R, NSE)
  4. correct_historical.py-> Additive mean bias correction for historical period
  5. correct_SSPsmodels.py-> Bias-correct future SSP projections (2015-2100)
  6. mapSSPs.py           -> Generate multi-decadal climatological projection maps
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

STEPS = [
    ("1. Standardizing ERA5 data", SCRIPTS_DIR / "align_era5.py"),
    ("2. Goodness of fit & Model ranking", SCRIPTS_DIR / "gf_test_and_rank.py"),
    ("3. Historical bias correction", SCRIPTS_DIR / "correct_historical.py"),
    ("4. Future SSP bias correction", SCRIPTS_DIR / "correct_SSPsmodels.py"),
    ("5. Generating projection maps", SCRIPTS_DIR / "mapSSPs.py"),
]

def main():
    print("=" * 65)
    print("  Punjab Climate Downscaling & Projection Pipeline")
    print("=" * 65)

    for desc, script in STEPS:
        if not script.exists():
            print(f"[ERROR] Script not found: {script.name}")
            continue

        print(f"\n>>> Running: {desc} ({script.name})...")
        res = subprocess.run([sys.executable, str(script)], cwd=str(BASE_DIR))
        if res.returncode != 0:
            print(f"[WARN] Step '{desc}' finished with return code {res.returncode}")
        else:
            print(f"[OK] {desc} completed successfully.")

    print("\n" + "=" * 65)
    print("  Pipeline execution complete!")
    print("=" * 65)

if __name__ == "__main__":
    main()
