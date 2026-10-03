import sys
import os
from pathlib import Path
import numpy as np
import geopandas as gpd
import rioxarray
import xarray as xr

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Dynamic paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"
SHAPEFILE_PATH = BASE_DIR / "gadm41_PAK_1.shp"

models = ["model2", "model3", "model4"]
ssp_scenarios = ["ssp126", "ssp245", "ssp370", "ssp585"]

# Load shapefile and filter for Punjab
print(f"Loading Punjab geometry from: {SHAPEFILE_PATH.name}")
gdf = gpd.read_file(SHAPEFILE_PATH)
punjab = gdf[gdf["NAME_1"] == "Punjab"].to_crs(epsg=4326)

# Variable names
temp_var = "tas"
precip_var = "pr"

# Target resolution matching ERA5 (0.25° x 0.25°)
target_resolution = 0.25
# Regional bounding grid for Punjab (covering ~68°E to 77°E, 26°N to 36°N)
target_lon = np.arange(68.0, 77.0, target_resolution)
target_lat = np.arange(26.0, 36.0, target_resolution)

for model in models:
    for ssp in ["historical"] + ssp_scenarios:
        base_path = MODELS_DIR / model / ssp
        output_path = OUTPUTS_DIR / model / ssp
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n--- Processing {model.upper()} | {ssp.upper()} ---")

        # ----------------- 1. Temperature (tas / ta) -----------------
        try:
            temp_file = base_path / f"{temp_var}.nc"
            if not temp_file.exists():
                alt_temp = base_path / "ta.nc"
                if alt_temp.exists():
                    temp_file = alt_temp

            if temp_file.exists():
                ds_temp = xr.open_dataset(temp_file, chunks={"time": 10})
                var_name = temp_var if temp_var in ds_temp else "ta"
                da_temp = ds_temp[var_name]

                # Slice historical period (1990–2014)
                if ssp == "historical":
                    da_temp = da_temp.sel(time=slice("1990-01-01", "2014-12-31"))

                # Standardize longitude dimension to [-180, 180] if model uses [0, 360]
                if float(da_temp.lon.max()) > 180:
                    da_temp = da_temp.assign_coords(lon=(((da_temp.lon + 180) % 360) - 180)).sortby("lon")

                # Resample onto target grid (0.25° resolution)
                da_temp_resampled = da_temp.interp(
                    lon=target_lon,
                    lat=target_lat,
                    method="linear"
                )

                # Convert from Kelvin to Celsius
                da_temp_resampled = da_temp_resampled - 273.15
                da_temp_resampled.attrs["units"] = "degC"

                # Set spatial coordinates and CRS
                da_temp_resampled = da_temp_resampled.rio.write_crs("EPSG:4326").rio.set_spatial_dims(x_dim="lon", y_dim="lat")
                clipped_temp = da_temp_resampled.rio.clip(punjab.geometry.values, punjab.crs, drop=True)
                clipped_temp.name = "tas"

                temp_out_file = output_path / f"{temp_var}_clipped.nc"
                clipped_temp.to_netcdf(temp_out_file)
                print(f"[OK] {model} [{ssp}] -> Temperature saved: {temp_out_file.name}")
            else:
                print(f"[WARN] No temperature file found for {model} [{ssp}]")
        except Exception as e:
            print(f"[ERROR] Temp processing failed for {model} [{ssp}]: {e}")

        # ----------------- 2. Precipitation (pr) -----------------
        try:
            pr_file = base_path / f"{precip_var}.nc"
            if pr_file.exists():
                ds_pr = xr.open_dataset(pr_file, chunks={"time": 10})
                da_pr = ds_pr[precip_var]

                # Slice historical period (1990–2014)
                if ssp == "historical":
                    da_pr = da_pr.sel(time=slice("1990-01-01", "2014-12-31"))

                # Standardize longitude dimension to [-180, 180] if model uses [0, 360]
                if float(da_pr.lon.max()) > 180:
                    da_pr = da_pr.assign_coords(lon=(((da_pr.lon + 180) % 360) - 180)).sortby("lon")

                # Resample onto target grid (0.25° resolution)
                da_pr_resampled = da_pr.interp(
                    lon=target_lon,
                    lat=target_lat,
                    method="linear"
                )

                # Convert flux (kg m-2 s-1 == mm/s) to monthly accumulation (mm/month)
                # 1 month ≈ 30 days = 30 * 86,400 seconds = 2,592,000 seconds
                seconds_per_month = 30 * 24 * 3600
                da_pr_resampled = da_pr_resampled * seconds_per_month
                da_pr_resampled.attrs["units"] = "mm/month"

                # Set spatial coordinates and CRS
                da_pr_resampled = da_pr_resampled.rio.write_crs("EPSG:4326").rio.set_spatial_dims(x_dim="lon", y_dim="lat")
                clipped_pr = da_pr_resampled.rio.clip(punjab.geometry.values, punjab.crs, drop=True)
                clipped_pr.name = "pr"

                pr_out_file = output_path / f"{precip_var}_clipped.nc"
                clipped_pr.to_netcdf(pr_out_file)
                print(f"[OK] {model} [{ssp}] -> Precipitation saved: {pr_out_file.name}")
            else:
                print(f"[WARN] No precipitation file found for {model} [{ssp}]")
        except Exception as e:
            print(f"[ERROR] Precipitation processing failed for {model} [{ssp}]: {e}")
