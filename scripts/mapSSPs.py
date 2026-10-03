import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
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
MAPS_DIR = BASE_DIR / "maps"
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# Models and SSPs
model_mapping = {
    "ACCESS-CM2": "model2",
    "CanESM5": "model3",
    "CanESM5-1": "model4"
}

ssps = ["ssp126", "ssp245", "ssp370", "ssp585"]

# Multi-decadal projection epochs
periods = {
    "2021-2040": ("2021-01-01", "2040-12-31"),
    "2041-2060": ("2041-01-01", "2060-12-31"),
    "2061-2080": ("2061-01-01", "2080-12-31"),
    "2081-2100": ("2081-01-01", "2100-12-31"),
}

for model_name, model_dir in model_mapping.items():
    for ssp in ssps:
        print(f"\nProcessing {model_name} [{ssp.upper()}]...")

        # Prefer bias-corrected projections; fallback to clipped if unavailable
        ssp_dir = OUTPUTS_DIR / model_dir / ssp
        tas_path = ssp_dir / "tas_ssp_bias_corrected.nc"
        if not tas_path.exists():
            tas_path = ssp_dir / "tas_clipped.nc"

        pr_path = ssp_dir / "pr_ssp_bias_corrected.nc"
        if not pr_path.exists():
            pr_path = ssp_dir / "pr_clipped.nc"

        if not tas_path.exists() or not pr_path.exists():
            print(f"[WARN] Missing datasets for {model_name} [{ssp}]. Skipping.")
            continue

        try:
            tas_ds = xr.open_dataset(tas_path)
            pr_ds = xr.open_dataset(pr_path)

            for period, (start_date, end_date) in periods.items():
                tas_period = tas_ds.sel(time=slice(start_date, end_date))
                pr_period = pr_ds.sel(time=slice(start_date, end_date))

                if len(tas_period.time) == 0 or len(pr_period.time) == 0:
                    continue

                tas_mean = tas_period["tas"].mean(dim="time")
                pr_mean = pr_period["pr"].mean(dim="time")

                plot_configs = [
                    ("Temperature", tas_mean, "coolwarm", "Mean Temperature (deg C)"),
                    ("Precipitation", pr_mean, "YlGnBu", "Mean Precipitation (mm/month)")
                ]

                for var_label, data, cmap, cbar_title in plot_configs:
                    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
                    mesh = data.plot(
                        ax=ax,
                        cmap=cmap,
                        cbar_kwargs={"label": cbar_title, "shrink": 0.8}
                    )
                    ax.set_title(f"Punjab: {model_name} | {ssp.upper()} ({period})\n{var_label}", fontsize=11, fontweight="bold")
                    ax.set_xlabel("Longitude (deg E)", fontsize=9)
                    ax.set_ylabel("Latitude (deg N)", fontsize=9)
                    plt.tight_layout()

                    map_filename = f"{model_name}_{ssp}_{period}_{var_label}.png"
                    map_filepath = MAPS_DIR / map_filename
                    plt.savefig(map_filepath)
                    plt.close()

            print(f"  [OK] Maps generated for {model_name} [{ssp.upper()}]")

        except Exception as e:
            print(f"[ERROR] Error generating maps for {model_name} [{ssp}]: {e}")

print(f"\n[OK] All spatial maps saved to: {MAPS_DIR}")
