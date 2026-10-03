import sys
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.stats import pearsonr

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Nash–Sutcliffe Efficiency (NSE)
def nse(obs, sim):
    denominator = np.sum((obs - np.mean(obs)) ** 2)
    if denominator == 0:
        return np.nan
    return 1 - (np.sum((obs - sim) ** 2) / denominator)

# Model names mapping
model_name_map = {
    "model2": "ACCESS-CM2",
    "model3": "CanESM5",
    "model4": "CanESM5-1"
}

# Dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"

models = ["model2", "model3", "model4"]
variables = ["tas", "pr"]

results = []

for var in variables:
    print(f"\n==== Goodness of Fit for {var.upper()} ====")
    aligned_era5_path = OUTPUTS_DIR / f"era5_punjab_{var}_aligned.nc"

    for model in models:
        model_path = OUTPUTS_DIR / model / "historical" / f"{var}_clipped.nc"
        era5_interp_path = OUTPUTS_DIR / f"era5_punjab_{var}_{model}_interpolated.nc"

        if not model_path.exists():
            print(f"[WARN] Model historical file missing: {model_path}")
            continue

        try:
            model_ds = xr.open_dataset(model_path)[var]

            # Load or dynamically interpolate ERA5 to match model grid
            if era5_interp_path.exists():
                era5_ds = xr.open_dataset(era5_interp_path)[var]
            elif aligned_era5_path.exists():
                era5_aligned = xr.open_dataset(aligned_era5_path)[var]
                era5_ds = era5_aligned.interp(lat=model_ds.lat, lon=model_ds.lon, method="linear")
            else:
                print(f"[ERROR] ERA5 reference not available for {var}.")
                continue

            model_vals = model_ds.values.flatten()
            era5_vals = era5_ds.values.flatten()

            # Align lengths and clean NaNs
            min_len = min(len(model_vals), len(era5_vals))
            model_vals = model_vals[:min_len]
            era5_vals = era5_vals[:min_len]

            mask = ~np.isnan(model_vals) & ~np.isnan(era5_vals)
            model_clean = model_vals[mask]
            era5_clean = era5_vals[mask]

            if len(model_clean) == 0:
                print(f"[WARN] No valid overlapping points for {model} ({var}).")
                continue

            mae = mean_absolute_error(era5_clean, model_clean)
            rmse = np.sqrt(mean_squared_error(era5_clean, model_clean))
            r_val, _ = pearsonr(era5_clean, model_clean)
            nse_val = nse(era5_clean, model_clean)

            print(f"\n{model_name_map.get(model, model)} ({var.upper()}):")
            print(f"  MAE  : {mae:.4f}")
            print(f"  RMSE : {rmse:.4f}")
            print(f"  R    : {r_val:.4f}")
            print(f"  NSE  : {nse_val:.4f}")

            results.append({
                "model": model_name_map.get(model, model),
                "model_id": model,
                "variable": var,
                "MAE": mae,
                "RMSE": rmse,
                "R": r_val,
                "NSE": nse_val
            })

        except Exception as e:
            print(f"[ERROR] Error evaluating {model} ({var}): {e}")

if results:
    df = pd.DataFrame(results)

    # Ranking: Lower RMSE is better, higher R and NSE are better
    df["rank_rmse"] = df.groupby("variable")["RMSE"].rank(method="min").astype(int)
    df["rank_r"] = df.groupby("variable")["R"].rank(ascending=False, method="min").astype(int)
    df["rank_nse"] = df.groupby("variable")["NSE"].rank(ascending=False, method="min").astype(int)

    # Combined overall rank
    df["overall_rank"] = df[["rank_rmse", "rank_r", "rank_nse"]].mean(axis=1).round().astype(int)

    # Save to CSV
    csv_path = OUTPUTS_DIR / "goodness_of_fit_results.csv"
    df.to_csv(csv_path, index=False)

    print("\n" + "=" * 50)
    print("FINAL MODEL RANKINGS SUMMARY")
    print("=" * 50)
    for v in variables:
        subset = df[df["variable"] == v].sort_values(by="overall_rank")
        print(f"\nVariable: {v.upper()}")
        print(subset[["model", "MAE", "RMSE", "R", "NSE", "overall_rank"]].to_string(index=False))

    print(f"\n[OK] Results saved to {csv_path.name}")
else:
    print("[WARN] No evaluation results generated.")
