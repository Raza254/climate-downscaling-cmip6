import sys
import os
from pathlib import Path
import geopandas as gpd
import rioxarray
import xarray as xr

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup dynamic project paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

input_file = BASE_DIR / "era5_pr.nc"
shapefile_path = BASE_DIR / "gadm41_PAK_1.shp"
output_file = OUTPUTS_DIR / "era5_punjab_pr_clipped.nc"

if not input_file.exists():
    print(f"[ERROR] ERA5 precipitation file not found: {input_file}")
    sys.exit(1)

print(f"Loading ERA5 precipitation from: {input_file.name}")
# Load ERA5 dataset lazily with dask chunking
ds = xr.open_dataset(input_file, chunks={"time": 10})

# Set CRS explicitly (ERA5 is in EPSG:4326)
ds = ds.rio.write_crs("EPSG:4326")

# Load shapefile and filter for Punjab
print(f"Filtering shapefile for Punjab region: {shapefile_path.name}")
gdf = gpd.read_file(shapefile_path)
punjab = gdf[gdf["NAME_1"] == "Punjab"]
punjab = punjab.to_crs(ds.rio.crs)

# Clip the precipitation data
print("Clipping precipitation data to Punjab boundary...")
clipped = ds.rio.clip(punjab.geometry.values, punjab.crs, drop=True)

# Save clipped data
clipped.to_netcdf(output_file)
print(f"[OK] ERA5 precipitation clipped and saved successfully to: {output_file.name}")
