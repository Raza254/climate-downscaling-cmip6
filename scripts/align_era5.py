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

tas_clipped_file = OUTPUTS_DIR / "era5_punjab_tas_clipped.nc"
pr_clipped_file = OUTPUTS_DIR / "era5_punjab_pr_clipped.nc"

print("Loading clipped ERA5 datasets...")
era5_tas = xr.open_dataset(tas_clipped_file)
era5_pr = xr.open_dataset(pr_clipped_file)

# Standardize dimensions to match CMIP6 conventions (valid_time -> time, longitude -> lon, latitude -> lat)
era5_tas = era5_tas.rename_dims({"valid_time": "time", "longitude": "lon", "latitude": "lat"})
era5_pr = era5_pr.rename_dims({"valid_time": "time", "longitude": "lon", "latitude": "lat"})

# Also rename coordinates if they exist
rename_coords_tas = {k: v for k, v in {"valid_time": "time", "longitude": "lon", "latitude": "lat"}.items() if k in era5_tas.coords}
rename_coords_pr = {k: v for k, v in {"valid_time": "time", "longitude": "lon", "latitude": "lat"}.items() if k in era5_pr.coords}

if rename_coords_tas:
    era5_tas = era5_tas.rename_vars(rename_coords_tas)
if rename_coords_pr:
    era5_pr = era5_pr.rename_vars(rename_coords_pr)

# 1. Temperature: Convert Kelvin to Celsius
era5_tas["tas"] = era5_tas["t2m"] - 273.15
era5_tas["tas"].attrs = {
    "units": "degC",
    "long_name": "Near-surface air temperature",
    "standard_name": "air_temperature"
}
era5_tas = era5_tas.drop_vars("t2m")

# 2. Precipitation: Convert ERA5 monthly mean daily accumulation (m/day) to monthly total (mm/month)
# ERA5 monthly averaged tp has units of meters per day.
# 1 m = 1000 mm. For an average month of 30 days: tp * 1000 * 30 = tp * 30000 mm/month.
days_per_month = 30
era5_pr["pr"] = era5_pr["tp"] * 1000.0 * days_per_month
era5_pr["pr"].attrs = {
    "units": "mm/month",
    "long_name": "Monthly total precipitation",
    "standard_name": "precipitation_amount"
}
era5_pr = era5_pr.drop_vars("tp")

# Save converted datasets
output_tas = OUTPUTS_DIR / "era5_punjab_tas_aligned.nc"
output_pr = OUTPUTS_DIR / "era5_punjab_pr_aligned.nc"

era5_tas.to_netcdf(output_tas)
era5_pr.to_netcdf(output_pr)

print(f"[OK] ERA5 conversion complete.")
print(f"     Saved: {output_tas.name}")
print(f"     Saved: {output_pr.name}")
