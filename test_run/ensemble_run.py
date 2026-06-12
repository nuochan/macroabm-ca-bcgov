"""Run N ensemble simulations with different seeds and visualize results.

Usage:
    uv run python test_run/ensemble_run.py                    # France, 50 runs
    uv run python test_run/ensemble_run.py CAN                # Canada, 50 runs
    uv run python test_run/ensemble_run.py FRA --n-runs 20    # Custom number of runs
    uv run python test_run/ensemble_run.py FRA --t-max 10     # Fewer timesteps for speed
    uv run python test_run/ensemble_run.py CAN_BC --n-runs 30

Outputs go to ``output/ensemble/``:
- ``ensemble_<country>_summary.csv`` — mean + std per timestep
- ``ensemble_<country>_timeseries.png`` — individual paths + mean ribbon plot
"""

import argparse
import sys
import time
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from macro_data import DataWrapper
from macro_data.configuration_utils import default_data_configuration
from macromodel.configurations import CountryConfiguration, SimulationConfiguration
from macromodel.simulation import Simulation


# ── CLI ────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Run ensemble of simulations with different seeds and plot results."
)
parser.add_argument("country", nargs="?", default="FRA", help="Country code (default: FRA)")
parser.add_argument("--n-runs", type=int, default=50, help="Number of ensemble members (default: 50)")
parser.add_argument("--t-max", type=int, default=20, help="Timesteps per run (default: 20)")
parser.add_argument("--scale", type=int, default=10_000, help="Scale factor (default: 10000)")
parser.add_argument("--output", default="output/ensemble", help="Output directory")
parser.add_argument(
    "--base-seed", type=int, default=42,
    help="First seed when --random-seeds is not set; seeds = base_seed + i (default: 42)"
)
parser.add_argument(
    "--random-seeds", action="store_true", default=False,
    help="Draw N random seeds instead of sequential ones. Overrides --base-seed."
)
args = parser.parse_args()

country = args.country.upper()
is_region = "_" in country
parent_country = country.split("_")[0] if is_region else country

# ── Resolve paths ──────────────────────────────────────────────
repo_root = Path(__file__).resolve().parent.parent
raw_data_dir = repo_root / "raw_data"
sample_data_dir = repo_root / "tests" / "test_macro_data" / "unit" / "sample_raw_data"
raw_data = raw_data_dir if raw_data_dir.exists() else sample_data_dir
output_dir = repo_root / args.output
output_dir.mkdir(parents=True, exist_ok=True)

# ── EU / proxy detection ────────────────────────────────────────
eu_countries = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
    "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
    "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE", "GBR",
}
needs_proxy = parent_country not in eu_countries
proxy_country = "FRA" if needs_proxy else None
proxy_dict = {parent_country: proxy_country} if proxy_country and needs_proxy else {}

# ── Auto-detect disaggregated Canada data ───────────────────────
disagg_cio_path = raw_data_dir / "icio" / "icio_can_2014_disagg.csv"
disagg_available = disagg_cio_path.exists()
is_canada = parent_country == "CAN"
use_disagg_can = (
    is_canada and proxy_country in eu_countries and disagg_available
)

# ── Data preprocessing (shared across all runs) ─────────────────
# ── Generate seeds ─────────────────────────────────────────────────
if args.random_seeds:
    rng = np.random.default_rng()
    seeds = [int(rng.integers(0, args.n_runs**2)) for _ in range(args.n_runs)]
    seed_label = f"{args.n_runs} random seeds"
else:
    seeds = [args.base_seed + i for i in range(args.n_runs)]
    seed_label = f"{seeds[0]} → {seeds[-1]} (sequential)"

print(f"=== Ensemble run: {country} × {args.n_runs} seeds ===")
print(f"  Timesteps: {args.t_max}  |  Scale: {args.scale:,}")
print(f"  Seeds: {seed_label}")
print(f"  Proxy: {proxy_country or 'None (EU country)'}")
print(f"  Disaggregated Canada: {use_disagg_can}")

t0_data = time.perf_counter()
if is_region:
    data_config = default_data_configuration(
        countries=[parent_country],
        proxy_country_dict=proxy_dict if proxy_dict else None,
        scale={parent_country: args.scale},
        seed=args.base_seed,
        use_disagg_can_2014_reader=use_disagg_can,
        aggregate_industries=not use_disagg_can,
    )
else:
    data_config = default_data_configuration(
        countries=[country],
        proxy_country_dict=proxy_dict if proxy_dict else None,
        scale={country: args.scale},
        seed=args.base_seed,
        use_disagg_can_2014_reader=use_disagg_can,
        aggregate_industries=not use_disagg_can,
    )
datawrapper = DataWrapper.from_config(data_config, raw_data, single_hfcs_survey=True)
print(f"  Data prepared in {time.perf_counter() - t0_data:.1f}s ({datawrapper.n_industries} industries)")

# ── Simulation config (baseline, seed will vary per run) ────────
n_industries = datawrapper.n_industries
country_config = (
    CountryConfiguration.n_industry_default(n_industries=n_industries)
    if use_disagg_can
    else CountryConfiguration()
)
sim_key = parent_country if is_region else country

# ── Run N simulations ──────────────────────────────────────────
all_dfs: list[pd.DataFrame] = []
run_times: list[float] = []

print(f"\nRunning {args.n_runs} simulations ...")
total_start = time.perf_counter()

for i in range(args.n_runs):
    seed = seeds[i]
    sim_config = SimulationConfiguration(
        country_configurations={sim_key: country_config},
        t_max=args.t_max,
        seed=seed,
    )

    t_run = time.perf_counter()
    sim = Simulation.from_datawrapper(datawrapper=datawrapper, simulation_configuration=sim_config)
    sim.run()
    elapsed = time.perf_counter() - t_run
    run_times.append(elapsed)

    df = sim.shallow_df_dict()[parent_country if is_region else country]
    df["seed"] = seed
    df["timestep"] = range(len(df))
    all_dfs.append(df)

    if (i + 1) % max(1, args.n_runs // 10) == 0 or i == 0:
        print(f"  [{i+1}/{args.n_runs}] seed={seed}  ({elapsed:.1f}s)  "
              f"remaining ~{np.mean(run_times) * (args.n_runs - i - 1):.0f}s")

total_elapsed = time.perf_counter() - total_start
print(f"\nDone.  Total: {total_elapsed:.1f}s  |  Avg/run: {np.mean(run_times):.1f}s  "
      f"|  Min: {min(run_times):.1f}s  |  Max: {max(run_times):.1f}s")

# ── Assemble into one long DataFrame ───────────────────────────
combined = pd.concat(all_dfs, ignore_index=True)

# ── Compute ensemble mean & std per timestep ───────────────────
metrics = [
    "Production", "Sales", "Wages", "Profits",
    "Household Consumption", "Government Consumption",
    "Imports", "Exports", "Gross Output",
    "Unemployment Rate", "CPI", "PPI",
]
available = [m for m in metrics if m in combined.columns]

summary_rows = []
for ts in range(args.t_max):
    row = {"timestep": ts}
    subset = combined[combined["timestep"] == ts]
    for m in available:
        row[f"{m}_mean"] = subset[m].mean()
        row[f"{m}_std"] = subset[m].std()
    summary_rows.append(row)
summary_df = pd.DataFrame(summary_rows)

csv_path = output_dir / f"ensemble_{country.lower()}_summary.csv"
summary_df.to_csv(csv_path, index=False)
print(f"\nSummary CSV → {csv_path}")

# ── Plot: individual runs + mean ribbon ────────────────────────
n_plots = len(available)
cols = 3
rows = (n_plots + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows))
axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

for idx, metric in enumerate(available):
    ax = axes[idx]

    # Plot each individual run as a thin faint line
    for seed_val, group in combined.groupby("seed"):
        ax.plot(group["timestep"], group[metric], alpha=0.15, color="steelblue", lw=0.6)

    # Ensemble mean as a bold red line
    mean_vals = summary_df[f"{metric}_mean"]
    std_vals = summary_df[f"{metric}_std"]
    ts_vals = summary_df["timestep"]

    ax.plot(ts_vals, mean_vals, color="crimson", lw=2.0, label="Mean")
    ax.fill_between(
        ts_vals,
        mean_vals - 2 * std_vals,
        mean_vals + 2 * std_vals,
        color="crimson", alpha=0.1, label="±2σ",
    )

    ax.set_title(metric, fontsize=11)
    ax.set_xlabel("Timestep")
    ax.grid(True, alpha=0.3)

# Hide unused subplots
for idx in range(len(available), len(axes)):
    axes[idx].set_visible(False)

# Single shared legend from last plot
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=9)

fig.suptitle(
    f"Ensemble Simulation — {country}  ({args.n_runs} runs, {seed_label})",
    fontsize=14, y=1.01,
)
plt.tight_layout()

png_path = output_dir / f"ensemble_{country.lower()}_timeseries.png"
fig.savefig(png_path, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"Timeseries plot → {png_path}")
