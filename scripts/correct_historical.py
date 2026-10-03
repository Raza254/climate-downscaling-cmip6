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
variables = ["tas", "pr"]

for var in variables:
    print(f"\n==================== BIAS CORRECTION: {var.upper()} ====================")

    aligned_era5_path = OUTPUTS_DIR / f"era5_punjab_{var}_aligned.nc"
    if not aligned_era5_path.exists():
        print(f"[WARN] Aligned ERA5 file not found: {aligned_era5_path.name}")

    for model in models:
        print(f"\n--- Model: {model.upper()} ---")

        model_path = OUTPUTS_DIR / model / "historical" / f"{var}_clipped.nc"
        era5_interp_path = OUTPUTS_DIR / f"era5_punjab_{var}_{model}_interpolated.nc"
        corrected_output_path = OUTPUTS_DIR / model / "historical" / f"{var}_corrected.nc"

        if not model_path.exists():
            print(f"[ERROR] Missing model file: {model_path}")
            continue

        try:
            model_ds = xr.open_dataset(model_path)
            model_data = model_ds[var]

            # Load or dynamically interpolate ERA5 to match model grid
            if era5_interp_path.exists():
                era5_ds = xr.open_dataset(era5_interp_path)
            elif aligned_era5_path.exists():
                era5_aligned = xr.open_dataset(aligned_era5_path)
                print(f"[INFO] Interpolating aligned ERA5 to match {model.upper()} grid...")
                era5_ds = era5_aligned.interp(lat=model_data.lat, lon=model_data.lon, method="linear")
            else:
                print(f"[ERROR] No ERA5 reference dataset found for {var}.")
                continue

            era5_data = era5_ds[var]

            # Calculate means over common spatial and temporal domain
            model_mean = float(model_data.mean().values)
            era5_mean = float(era5_data.mean().values)
            bias = model_mean - era5_mean

            # Additive mean bias correction: Model_corrected = Model - (Mean_model - Mean_obs)
            corrected_data = model_data - bias

            # For precipitation, ensure non-negative physical values
            if var == "pr":
                corrected_data = corrected_data.clip(min=0)

            # Save corrected dataset
            corrected_ds = model_ds.copy()
            corrected_ds[var] = corrected_data
            corrected_ds[var].attrs["bias_correction_applied"] = f"Additive Mean Adjustment (bias = {bias:.4f})"
            corrected_ds.to_netcdf(corrected_output_path)

            print(f"ERA5 Reference Mean:      {era5_mean:.3f}")
            print(f"{model.upper()} Uncorrected Mean: {model_mean:.3f}")
            print(f"{model.upper()} Calculated Bias:    {bias:.3f}")
            print(f"{model.upper()} Corrected Mean:   {float(corrected_data.mean().values):.3f}")
            print(f"[OK] Saved corrected {var.upper()} to: {corrected_output_path.name}")

        except Exception as e:
            print(f"[ERROR] Error processing {model} for {var}: {e}")
