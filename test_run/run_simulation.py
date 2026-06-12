"""Unified simulation runner for any country or subnational region.

Usage:
    uv run python run_simulation.py                    # France (default)
    uv run python run_simulation.py DEU                # Germany (EU - no proxy needed)
    uv run python run_simulation.py CAN                # Canada (auto-detects disaggregated if raw_data present)
    uv run python run_simulation.py CAN --aggregated   # Canada with 18 aggregated industries
    uv run python run_simulation.py CAN --proxy DEU    # Canada with Germany as proxy
    uv run python run_simulation.py USA --proxy FRA    # USA with France as proxy
    uv run python run_simulation.py GBR --proxy DEU    # UK with Germany as proxy
    uv run python run_simulation.py CAN --scale 5000   # Custom scale
    uv run python run_simulation.py CAN_BC             # BC provincial economy (auto progressive PIT)
    uv run python run_simulation.py CAN_BC --national  # BC using national CAN table (no inter-prov. trade)
    uv run python run_simulation.py CAN_ON --scale 2000

CAN_BC (and other CAN_XX regions) automatically activate BC's progressive
personal income tax schedule from ``spoof_data/freda/BC_PIT_2014.csv``
with compound CPI inflation indexing.

If ``raw_data/icio/icio_2014_can_provinces_remapped.csv`` exists, CAN regions
default to the full provincial simulation (10 provinces, 50 industries) with
inter-provincial trade.  Use --national to fall back to the single-country
national IO table (46 industries) instead.  Provincial mode defaults to a
scale divisor of 500 when --scale is not explicitly supplied.

If ``raw_data/icio/icio_can_2014_disagg.csv`` exists, ``CAN`` (national) uses
46 disaggregated industries by default.  Use --aggregated for 18 sectors.
"""
import argparse
import logging
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# ── Suppress expected noise in provincial mode ────────────────
# 10 provinces × 50 industries = sparse IO table with legitimate
# zero-value cells throughout.  These produce harmless warnings.
np.seterr(divide="ignore", invalid="ignore")
warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
warnings.filterwarnings("ignore", message=".*Overwriting Consumption.*")
warnings.filterwarnings("ignore", message="GDP output/expenditure mismatch > 5%:.*")


def _suppress_expected_proxy_logs(record: logging.LogRecord) -> bool:
    return record.getMessage() != "Overwriting Consumption Weights by Income with French Data"


logging.getLogger().addFilter(_suppress_expected_proxy_logs)

from macro_data import DataWrapper
from macro_data.configuration.countries import Country as Ctry
from macro_data.configuration.region import Region
from macro_data.configuration_utils import default_data_configuration
from macro_data.readers.taxation.personal_income_tax.pit_schedule import PITSchedule
from macromodel.configurations import CountryConfiguration, SimulationConfiguration
from macromodel.configurations.central_government_configuration import CentralGovernmentConfiguration
from macromodel.simulation import Simulation


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def main():
    total_start = time.perf_counter()
    
    parser = argparse.ArgumentParser(description="Run macroeconomic simulation for a country.")
    parser.add_argument("country", nargs="?", default="FRA", help="Country code (default: FRA)")
    parser.add_argument("--proxy", default=None, help="Proxy country for non-EU countries (default: FRA for non-EU)")
    parser.add_argument(
        "--scale", type=int, default=10_000,
        help="Population/economy divisor: lower values create more synthetic agents (default: 10000)."
    )
    parser.add_argument("--t-max", type=int, default=20, help="Number of timesteps (default: 20)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (default: 0)")
    parser.add_argument("--output", default="output/single_run", help="Output directory (default: output/single_run)")
    parser.add_argument(
        "--aggregated", action="store_true", default=False,
        help="Force aggregated industries (18 sectors) even when disaggregated data is available. "
             "Applies to Canada and its regions (CAN_BC, CAN_ON, etc.)."
    )
    parser.add_argument(
        "--national", action="store_true", default=False,
        help="Use the national IO table (46 industries) instead of the provincial one "
             "for CAN regions.  Only meaningful for CAN_BC, CAN_ON, etc.; ignored otherwise."
    )
    parser.add_argument(
        "--save-all", action="store_true", default=False,
        help="Save all provinces in the H5 output (default: only the target province "
             "in provincial mode).  Ignored for non-provincial runs."
    )
    args = parser.parse_args()

    country = args.country.upper()
    proxy = args.proxy.upper() if args.proxy else None

    # Detect region codes (e.g. "CAN_BC" → parent "CAN")
    is_region = "_" in country
    parent_country = country.split("_")[0] if is_region else country

    # Resolve paths
    repo_root = Path(__file__).resolve().parent.parent
    raw_data_dir = repo_root / "raw_data"
    sample_data_dir = repo_root / "tests/test_macro_data/unit/sample_raw_data"
    raw_data = raw_data_dir if raw_data_dir.exists() else sample_data_dir
    output_dir = repo_root / args.output
    output_dir.mkdir(exist_ok=True)

    # Determine if country needs proxy (non-EU countries)
    # EU28 countries as of 2014 (includes UK which was still EU member)
    eu_countries = {
        "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
        "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE", "GBR"
    }
    
    needs_proxy = parent_country not in eu_countries
    proxy_country = proxy or ("FRA" if needs_proxy else None)

    print(f"=== Running simulation for {country} ===")
    if is_region:
        print(f"  Region of: {parent_country}")
    print(f"  Scale: {args.scale:,}")
    print(f"  Timesteps: {args.t_max}")
    print(f"  Seed: {args.seed}")
    
    if needs_proxy:
        print(f"  Proxy country: {proxy_country} (required for non-EU)")
    else:
        print(f"  Proxy country: {proxy_country or 'None (EU country)'}")

    # Build proxy dict — keyed by parent country
    if proxy_country and needs_proxy:
        proxy_dict = {parent_country: proxy_country}
    else:
        proxy_dict = {}

    # Auto-detect whether disaggregated Canada ICIO data is available.
    disagg_cio_path = raw_data_dir / "icio" / "icio_can_2014_disagg.csv"
    disagg_available = disagg_cio_path.exists()

    # Auto-detect provincial IO table.
    prov_remapped_path = raw_data_dir / "icio" / "icio_2014_can_provinces_remapped.csv"
    prov_original_path = raw_data_dir / "icio" / "icio_2014_can_provinces.csv"
    provincial_available = prov_remapped_path.exists() or prov_original_path.exists()

    is_canada = parent_country == "CAN"

    # ── Provincial mode: CAN regions default to 10-province simulation
    # when provincial IO data is available.  --national forces fallback.
    use_provincial = (
        is_canada
        and is_region
        and provincial_available
        and not args.national
    )

    # ── National disaggregated mode (CAN only, not regions) ──
    use_disagg_can = (
        is_canada
        and not use_provincial
        and proxy_country in eu_countries
        and disagg_available
        and not args.aggregated
    )

    # ── Scale: lower = more agents.  The scale is a divisor (e.g.
    # n_households ≈ real_households / scale).  Provincial mode needs
    # enough agents for 10 provinces × 50 industries, but too many agents
    # can exhaust memory in the goods market.
    _DEFAULT_SCALE = 10_000
    _PROVINCIAL_DEFAULT_SCALE = 500
    if use_provincial and args.scale == _DEFAULT_SCALE:
        print(
            f"  NOTE: Auto-adjusting provincial scale from {args.scale:,} to "
            f"{_PROVINCIAL_DEFAULT_SCALE:,} (lower divisor = more agents)."
        )
        args.scale = _PROVINCIAL_DEFAULT_SCALE
    elif use_provincial and args.scale < 500:
        warnings.warn(
            f"Provincial scale {args.scale:,} creates many agents and may exhaust "
            f"memory during goods-market setup.  Try --scale 500 or higher if this run fails.",
            UserWarning,
        )
    elif use_provincial and args.scale > 1_000:
        warnings.warn(
            f"Provincial scale {args.scale:,} may create too few synthetic agents "
            f"for small provinces/industries.  Try --scale 500 if this run fails.",
            UserWarning,
        )

    # ── Mode announcements ──
    if use_provincial:
        if args.aggregated:
            warnings.warn("--aggregated ignored in provincial mode.", UserWarning)
        print("  Note: Provincial simulation (10 provinces, auto-detected)")
        print("  Note: Consumption weights by income for all provinces use French proxy data")
        print("  Note: GDP output/expenditure mismatch warnings are summarized and suppressed in provincial mode")
    elif is_canada:
        if is_region and args.national:
            print("  Note: Forcing national-table fallback (--national)")
        elif args.aggregated:
            if disagg_available:
                warnings.warn(
                    "Disaggregated Canada ICIO data is available but --aggregated "
                    "forces 18 aggregated sectors instead of 46.",
                    UserWarning,
                )
            print("  Note: Forcing aggregated Canada configuration (--aggregated)")
        elif use_disagg_can:
            print("  Note: Using disaggregated Canada energy sector reader (auto-detected)")
        elif not disagg_available:
            warnings.warn(
                f"Disaggregated Canada ICIO data not found at {disagg_cio_path}. "
                f"Falling back to 18 aggregated sectors.",
                UserWarning,
            )
            print("  Note: Disaggregated data not found — using standard Canada configuration")
    elif args.aggregated:
        warnings.warn(
            "--aggregated flag has no effect for non-Canada countries. "
            f"'{country}' is not a Canada run.",
            UserWarning,
        )

    # 1. Data preprocessing
    print("\n[1/4] Preprocessing data...")
    step_start = time.perf_counter()
    
    if use_provincial:
        # ── Provincial path (10 provinces, 50 industries) ──
        can = Ctry("CAN")
        fra = Ctry("FRA")
        data_config = default_data_configuration(
            countries=[can], proxy_country_dict={can: fra},
            scale={can: args.scale}, seed=args.seed,
            aggregate_industries=False,
        )
        base_conf = data_config.country_configs[can]

        provinces = [
            Region.from_code("CAN_AB", "Alberta"),
            Region.from_code("CAN_BC", "British Columbia"),
            Region.from_code("CAN_MB", "Manitoba"),
            Region.from_code("CAN_NB", "New Brunswick"),
            Region.from_code("CAN_NL", "Newfoundland and Labrador"),
            Region.from_code("CAN_NS", "Nova Scotia"),
            Region.from_code("CAN_ON", "Ontario"),
            Region.from_code("CAN_PE", "Prince Edward Island"),
            Region.from_code("CAN_QC", "Quebec"),
            Region.from_code("CAN_SK", "Saskatchewan"),
        ]
        for p in provinces:
            data_config.country_configs[p] = base_conf
            data_config.country_configs[p].eu_proxy_country = fra
        data_config.aggregation_structure = {can: provinces}

        datawrapper = DataWrapper.from_config(data_config, raw_data, single_hfcs_survey=True)

    elif is_region:
        # ── Subnational region path (national-table fallback) ──
        print(f"  Running as parent country {parent_country} (region label: {country})")
        data_config = default_data_configuration(
            countries=[parent_country],
            proxy_country_dict=proxy_dict if proxy_dict else None,
            scale={parent_country: args.scale},
            seed=args.seed,
            use_disagg_can_2014_reader=use_disagg_can,
            aggregate_industries=not use_disagg_can,
        )
        datawrapper = DataWrapper.from_config(data_config, raw_data, single_hfcs_survey=True)
    else:
        # ── Country path (backward compatible) ──
        data_config = default_data_configuration(
            countries=[country],
            proxy_country_dict=proxy_dict if proxy_dict else None,
            scale={country: args.scale},
            seed=args.seed,
            use_disagg_can_2014_reader=use_disagg_can,
            aggregate_industries=not use_disagg_can,
        )
        datawrapper = DataWrapper.from_config(data_config, raw_data, single_hfcs_survey=True)
    step_elapsed = time.perf_counter() - step_start
    print(f"  Created {datawrapper.n_industries} industries in {format_duration(step_elapsed)}")

    # 2. Simulation configuration
    step_start = time.perf_counter()
    print("\n[2/4] Configuring simulation...")
    n_industries = datawrapper.n_industries

    if n_industries > 18:
        country_config = CountryConfiguration.n_industry_default(n_industries=n_industries)
    else:
        country_config = CountryConfiguration()

    # ── Progressive PIT (auto-activated for CAN_BC) ────────────
    if country == "CAN_BC":
        print(f"\n  Activating BC progressive PIT schedule ...")
        schedule = PITSchedule.from_name_with_cpi("BC_PIT_2014.csv")
        cpi_years = sorted(schedule.cpi_map)
        print(f"  CPI inflation data: {cpi_years[0]}–{cpi_years[-1]} ({len(cpi_years)} years)")
        thresholds, rates, _, _ = schedule.get_brackets(tax_year=schedule.base_year)

        brackets = [(float(thresholds[i]), float(rates[i])) for i in range(len(thresholds))]
        country_config.central_government = CentralGovernmentConfiguration(
            pit_brackets=brackets,
            pit_taxable_income_deductions=schedule.basic_deduction,
            functions=country_config.central_government.functions,
        )
        if schedule.basic_deduction is not None:
            print(f"  Basic personal amount (deduction from taxable income): ${schedule.basic_deduction:,.0f}")
        print(f"  Progressive PIT: {len(brackets)} brackets")
        for i, (thresh, rate) in enumerate(brackets):
            print(f"    Bracket {i+1}: up to {thresh:>12,.0f} @ {rate:.1%}")

    sim_key = parent_country if is_region else country

    if use_provincial:
        # All 10 provinces need a config (not just the target).
        all_provinces = [
            Region.from_code("CAN_AB", "Alberta"),
            Region.from_code("CAN_BC", "British Columbia"),
            Region.from_code("CAN_MB", "Manitoba"),
            Region.from_code("CAN_NB", "New Brunswick"),
            Region.from_code("CAN_NL", "Newfoundland and Labrador"),
            Region.from_code("CAN_NS", "Nova Scotia"),
            Region.from_code("CAN_ON", "Ontario"),
            Region.from_code("CAN_PE", "Prince Edward Island"),
            Region.from_code("CAN_QC", "Quebec"),
            Region.from_code("CAN_SK", "Saskatchewan"),
        ]
        default_cc = CountryConfiguration.n_industry_default(n_industries=n_industries)
        all_configs = {p: default_cc for p in all_provinces}
        for p in all_provinces:
            if str(p) == country:
                all_configs[p] = country_config  # progressive PIT on target
                sim_key = str(p)
                break
    else:
        all_configs = {sim_key: country_config}

    sim_config = SimulationConfiguration(
        country_configurations=all_configs,
        t_max=args.t_max,
        seed=args.seed,
    )
    step_elapsed = time.perf_counter() - step_start
    print(f"  Configuration complete in {format_duration(step_elapsed)}")

    # 3. Run simulation
    print("\n[3/4] Running simulation...")
    step_start = time.perf_counter()
    simulation = Simulation.from_datawrapper(
        datawrapper=datawrapper, 
        simulation_configuration=sim_config
    )

    # ── CPI-index PIT bracket thresholds every year ──────────
    # BC indexes its income-tax brackets to CPI every year.
    # We fire on month==1 (January) so the hook works correctly
    # regardless of the timestep increment (monthly / quarterly / annual).
    if country == "CAN_BC":
        _schedule = schedule          # capture for closure
        _sim_key = sim_key
        def _index_pit_brackets(_sim, t, year, month):
            if t > 0 and month == 1:
                cg = _sim.countries[_sim_key].central_government
                cg.step_pit_brackets(
                    tax_year=year,
                    cpi_map=_schedule.cpi_map,
                    base_year=_schedule.base_year,
                )
        simulation.posthooks.append(_index_pit_brackets)

    try:
        simulation.run()
    except MemoryError as exc:
        if use_provincial:
            raise MemoryError(
                "Provincial simulation ran out of memory during goods-market setup. "
                "Increase the scale divisor to create fewer agents, e.g. --scale 750 "
                "or --scale 1000."
            ) from exc
        raise
    step_elapsed = time.perf_counter() - step_start
    print(f"  Simulation complete in {format_duration(step_elapsed)}")
    print(f"  Average per timestep: {step_elapsed / args.t_max:.2f}s")

    # 4. Save results
    print("\n[4/4] Saving results...")
    sim_file = output_dir / f"sim_{country.lower()}.h5"
    shallow_file = output_dir / f"sim_{country.lower()}_shallow.h5"
    
    # In provincial mode, only save the target province unless --save-all.
    _save_countries = None if (args.save_all or not use_provincial) else [sim_key]
    simulation.save(save_dir=output_dir, file_name=sim_file.name, countries=_save_countries)
    simulation.shallow_hdf_save(save_dir=output_dir, file_name=shallow_file.name, countries=_save_countries)
    
    print(f"  Full output: {sim_file}")
    print(f"  Shallow output: {shallow_file}")

    # Print summary
    results = simulation.shallow_df_dict()
    summary_key = sim_key
    print(f"\n=== Summary for {country} ===")
    if summary_key in results:
        print(results[summary_key].head())
    else:
        print(f"  (No summary for '{summary_key}'; available: {sorted(results.keys())})")

    # Final timing
    total_elapsed = time.perf_counter() - total_start
    print(f"\n=== Timing Summary ===")
    print(f"  Total elapsed: {format_duration(total_elapsed)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
