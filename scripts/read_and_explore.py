import sys
from pathlib import Path
import xarray as xr

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Dynamic project paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
LOG_DIR = OUTPUTS_DIR / "clipped_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 1. Log ERA5 clipped temperature
era_temp_file = OUTPUTS_DIR / "era5_punjab_tas_clipped.nc"
if era_temp_file.exists():
    try:
        era_temp = xr.open_dataset(era_temp_file)
        with open(LOG_DIR / "era5_tas_clipped_log.txt", "w") as f:
            f.write("ERA5 Temperature Dataset (Clipped):\n\n")
            f.write(str(era_temp))
        print(f"[OK] Logged {era_temp_file.name}")
    except Exception as e:
        print(f"[ERROR] Failed to log ERA5 temperature: {e}")

# 2. Log ERA5 clipped precipitation
era_pr_file = OUTPUTS_DIR / "era5_punjab_pr_clipped.nc"
if era_pr_file.exists():
    try:
        era_pr = xr.open_dataset(era_pr_file)
        with open(LOG_DIR / "era5_pr_clipped_log.txt", "w") as f:
            f.write("ERA5 Precipitation Dataset (Clipped):\n\n")
            f.write(str(era_pr))
        print(f"[OK] Logged {era_pr_file.name}")
    except Exception as e:
        print(f"[ERROR] Failed to log ERA5 precipitation: {e}")

# 3. Models and scenarios logs
models = ["model2", "model3", "model4"]
scenarios = ["historical", "ssp126", "ssp245", "ssp370", "ssp585"]

for model in models:
    log_file = LOG_DIR / f"{model}_clipped_summary.txt"
    with open(log_file, "w") as f:
        f.write(f"{model.upper()} CLIPPED DATA SUMMARY\n\n")

        for scenario in scenarios:
            tas_path = OUTPUTS_DIR / model / scenario / "tas_clipped.nc"
            pr_path = OUTPUTS_DIR / model / scenario / "pr_clipped.nc"

            f.write(f"--- {scenario.upper()} ---\n\n")

            if tas_path.exists():
                try:
                    tas_ds = xr.open_dataset(tas_path)
                    f.write("Temperature Dataset (tas_clipped.nc):\n")
                    f.write(str(tas_ds))
                except Exception as e:
                    f.write(f"[ERROR] Failed to open tas_clipped.nc: {e}\n")
            else:
                f.write("tas_clipped.nc not found\n")

            f.write("\n")

            if pr_path.exists():
                try:
                    pr_ds = xr.open_dataset(pr_path)
                    f.write("Precipitation Dataset (pr_clipped.nc):\n")
                    f.write(str(pr_ds))
                except Exception as e:
                    f.write(f"[ERROR] Failed to open pr_clipped.nc: {e}\n")
            else:
                f.write("pr_clipped.nc not found\n")

            f.write("\n" + "-" * 50 + "\n\n")

    print(f"[OK] Logged all scenarios for {model}")
