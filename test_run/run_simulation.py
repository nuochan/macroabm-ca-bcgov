"""Unified simulation runner for any country.

Usage:
    uv run python run_simulation.py                    # France (default)
    uv run python run_simulation.py CAN                # Canada (auto-uses FRA as proxy)
    uv run python run_simulation.py USA --proxy FRA    # USA with France as proxy
    uv run python run_simulation.py CAN --proxy FRA --scale 5000  # Custom scale
"""
import argparse
import sys
from pathlib import Path

from macro_data import DataWrapper
from macro_data.configuration_utils import default_data_configuration
from macromodel.configurations import CountryConfiguration, SimulationConfiguration
from macromodel.simulation import Simulation


def main():
    parser = argparse.ArgumentParser(description="Run macroeconomic simulation for a country.")
    parser.add_argument("country", nargs="?", default="FRA", help="Country code (default: FRA)")
    parser.add_argument("--proxy", default=None, help="Proxy country for non-EU countries (default: FRA for non-EU)")
    parser.add_argument("--scale", type=int, default=10_000, help="Scale factor (default: 10000)")
    parser.add_argument("--t-max", type=int, default=20, help="Number of timesteps (default: 20)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (default: 0)")
    parser.add_argument("--output", default="output", help="Output directory (default: output)")
    args = parser.parse_args()

    country = args.country.upper()
    proxy = args.proxy.upper() if args.proxy else None

    # Resolve paths
    repo_root = Path(__file__).resolve().parent.parent
    raw_data = repo_root / "tests/test_macro_data/unit/sample_raw_data"
    output_dir = repo_root / args.output
    output_dir.mkdir(exist_ok=True)

    # Determine if country needs proxy (non-EU countries)
    eu_countries = {"FRA", "DEU", "ITA", "ESP", "NLD", "BEL", "AUT", "FIN", "IRL", "PRT", "GRC", "SVK", "SVN", "EST", "LVA", "LTU", "LUX", "MLT", "CYP"}
    
    needs_proxy = country not in eu_countries
    proxy_country = proxy or ("FRA" if needs_proxy else None)

    print(f"=== Running simulation for {country} ===")
    print(f"  Scale: {args.scale:,}")
    print(f"  Timesteps: {args.t_max}")
    print(f"  Seed: {args.seed}")
    
    if needs_proxy:
        print(f"  Proxy country: {proxy_country} (required for non-EU)")
    else:
        print(f"  Proxy country: {proxy_country or 'None (EU country)'}")

    # Build proxy dict if needed
    proxy_dict = {country: proxy_country} if proxy_country and needs_proxy else {}

    # Special handling for Canada
    is_canada = country == "CAN"
    use_disagg_can = is_canada and proxy_dict == {"CAN": "FRA"}

    if is_canada and not use_disagg_can:
        print("  Note: Using standard Canada configuration")
    elif use_disagg_can:
        print("  Note: Using disaggregated Canada energy sector reader")

    # 1. Data preprocessing
    print("\n[1/4] Preprocessing data...")
    data_config = default_data_configuration(
        countries=[country],
        proxy_country_dict=proxy_dict if proxy_dict else None,
        scale={country: args.scale},
        seed=args.seed,
        use_disagg_can_2014_reader=use_disagg_can,
        aggregate_industries=not use_disagg_can,  # Canada disagg needs non-aggregated
    )
    datawrapper = DataWrapper.from_config(data_config, raw_data, single_hfcs_survey=True)
    print(f"  Created {datawrapper.n_industries} industries")

    # 2. Simulation configuration
    print("\n[2/4] Configuring simulation...")
    n_industries = datawrapper.n_industries
    
    if use_disagg_can:
        # Canada needs special industry configuration
        country_config = CountryConfiguration.n_industry_default(n_industries=n_industries)
    else:
        country_config = CountryConfiguration()

    sim_config = SimulationConfiguration(
        country_configurations={country: country_config},
        t_max=args.t_max,
        seed=args.seed,
    )

    # 3. Run simulation
    print("\n[3/4] Running simulation...")
    simulation = Simulation.from_datawrapper(
        datawrapper=datawrapper, 
        simulation_configuration=sim_config
    )
    simulation.run()
    print("  Simulation complete!")

    # 4. Save results
    print("\n[4/4] Saving results...")
    sim_file = output_dir / f"sim_{country.lower()}.h5"
    shallow_file = output_dir / f"sim_{country.lower()}_shallow.h5"
    
    simulation.save(save_dir=output_dir, file_name=sim_file.name)
    simulation.shallow_hdf_save(save_dir=output_dir, file_name=shallow_file.name)
    
    print(f"  Full output: {sim_file}")
    print(f"  Shallow output: {shallow_file}")

    # Print summary
    results = simulation.shallow_df_dict()
    print(f"\n=== Summary for {country} ===")
    print(results[country].head())

    return 0


if __name__ == "__main__":
    sys.exit(main())
