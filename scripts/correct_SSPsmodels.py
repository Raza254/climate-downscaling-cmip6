import sys
from pathlib import Path
import xarray as xr
import numpy as np

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Dynamic project paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"

models = ["model2", "model3", "model4"]
ssps = ["ssp126", "ssp245", "ssp370", "ssp585"]
variables = ["tas", "pr"]

for var in variables:
    print(f"\n==================== FUTURE SSP BIAS CORRECTION: {var.upper()} ====================")

    for model in models:
        print(f"\n=== Model: {model.upper()} ===")

        hist_raw_path = OUTPUTS_DIR / model / "historical" / f"{var}_clipped.nc"
        hist_corrected_path = OUTPUTS_DIR / model / "historical" / f"{var}_corrected.nc"

        if not hist_raw_path.exists() or not hist_corrected_path.exists():
            print(f"[WARN] Missing historical files for {model.upper()} ({var}). Skipping.")
            continue

        try:
            hist_raw_ds = xr.open_dataset(hist_raw_path)
            hist_corrected_ds = xr.open_dataset(hist_corrected_path)

            hist_raw_mean = float(hist_raw_ds[var].mean().values)
            hist_corrected_mean = float(hist_corrected_ds[var].mean().values)

            # Historical baseline bias: difference between raw model and reference
            hist_bias = hist_raw_mean - hist_corrected_mean
            print(f"Historical Raw Mean:       {hist_raw_mean:.3f}")
            print(f"Historical Corrected Mean: {hist_corrected_mean:.3f}")
            print(f"Model Historical Bias:     {hist_bias:.3f}")

            for ssp in ssps:
                ssp_raw_path = OUTPUTS_DIR / model / ssp / f"{var}_clipped.nc"
                corrected_ssp_path = OUTPUTS_DIR / model / ssp / f"{var}_ssp_bias_corrected.nc"

                if not ssp_raw_path.exists():
                    print(f"[WARN] Missing SSP file: {ssp_raw_path.name}")
                    continue

                ssp_ds = xr.open_dataset(ssp_raw_path)
                ssp_data = ssp_ds[var]
                ssp_raw_mean = float(ssp_data.mean().values)

                # Correct future projections using historical bias
                # Preserves future climate change signal while adjusting baseline offset:
                # SSP_corrected = SSP_raw - (Model_hist_mean - Reference_hist_mean)
                corrected_ssp = ssp_data - hist_bias

                if var == "pr":
                    corrected_ssp = corrected_ssp.clip(min=0)

                corrected_ds = ssp_ds.copy()
                corrected_ds[var] = corrected_ssp
                corrected_ds[var].attrs["bias_correction_applied"] = f"Historical Bias Adjustment (bias = {hist_bias:.4f})"
                corrected_ds.to_netcdf(corrected_ssp_path)

                corrected_ssp_mean = float(corrected_ssp.mean().values)
                print(f"  [{ssp.upper()}] Raw Mean: {ssp_raw_mean:.3f} -> Corrected Mean: {corrected_ssp_mean:.3f} (Signal: {corrected_ssp_mean - hist_corrected_mean:+.3f})")

        except Exception as e:
            print(f"[ERROR] Error processing {model.upper()} SSPs for {var}: {e}")
