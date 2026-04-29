"""Reader and container for exogenous energy price data."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class ExoPrices:
    """Container for exogenous energy price paths.

    Holds fossil fuel and electricity price trajectories from an external
    model (e.g. CIMS), together with the industry-name-to-CSV-row mappings
    that connect each model industry to the correct row in each price file.

    The mapping keys are industry names (strings) so the price setter can
    look up array indices at runtime — no hardcoded positional indices.

    Attributes:
        fossil_prices: DataFrame of fossil fuel price projections.
            Row 0 contains the years; subsequent rows contain $/GJ values.
        electricity_prices: DataFrame of electricity price projections,
            same layout as fossil_prices.
        fossil_sector_rows: Maps each industry name to its row index in
            fossil_prices (e.g. {"B05a Coal mining": 22}).
        electricity_sector_rows: Maps each industry name to its row index
            in electricity_prices (e.g. {"D01a Electricity": 4}).
        petroleum_crude_sector: Industry name for petroleum crude, whose
            price series comes from petroleum_crude_data rather than the
            fossil CSV (because CIMS does not export it directly).
        petroleum_crude_data: Raw price series for petroleum crude as
            {"years": [2014, 2016, ...], "prices": [61, 53, ...]}.
        initial_year: Base year for price normalisation. Set to the
            simulation's initial_year before passing to Firms.
        initial_model_prices: Per-industry base prices from the model
            (average_initial_price array). Set from Country before Firms
            is constructed so the price setter can normalise correctly.
    """

    fossil_prices: Optional[pd.DataFrame] = None
    electricity_prices: Optional[pd.DataFrame] = None
    fossil_sector_rows: dict[str, int] = field(default_factory=dict)
    electricity_sector_rows: dict[str, int] = field(default_factory=dict)
    petroleum_crude_sector: Optional[str] = None
    petroleum_crude_data: Optional[dict] = None
    initial_year: int = 2014
    initial_model_prices: Optional[np.ndarray] = None

    @property
    def values_dictionary(self) -> dict:
        """Dict-based access to the price DataFrames."""
        return {
            "fossil_prices": self.fossil_prices,
            "electricity_prices": self.electricity_prices,
        }

    @classmethod
    def from_reader(
        cls,
        reader: ExoPricesReader,
        fossil_sector_rows: Optional[dict[str, int]] = None,
        electricity_sector_rows: Optional[dict[str, int]] = None,
        petroleum_crude_sector: Optional[str] = None,
        petroleum_crude_data: Optional[dict] = None,
        initial_year: int = 2014,
    ) -> ExoPrices:
        """Build an ExoPrices container from a reader and industry mappings.

        Args:
            reader: Loaded ExoPricesReader.
            fossil_sector_rows: Maps industry name → row index in fossil CSV.
            electricity_sector_rows: Maps industry name → row index in
                electricity CSV.
            petroleum_crude_sector: Industry name for petroleum crude.
            petroleum_crude_data: {"years": [...], "prices": [...]} for
                petroleum crude (not available in fossil CSV).
            initial_year: Base year for price normalisation.

        Returns:
            ExoPrices container ready to be passed to Firms.
        """
        return cls(
            fossil_prices=reader.fossil_prices,
            electricity_prices=reader.electricity_prices,
            fossil_sector_rows=fossil_sector_rows or {},
            electricity_sector_rows=electricity_sector_rows or {},
            petroleum_crude_sector=petroleum_crude_sector,
            petroleum_crude_data=petroleum_crude_data,
            initial_year=initial_year,
        )


@dataclass
class ExoPricesReader:
    """Reader for exogenous fossil fuel and electricity price CSVs.

    Attributes:
        fossil_prices: DataFrame with fossil fuel price projections.
        electricity_prices: DataFrame with electricity price projections.
    """

    fossil_prices: Optional[pd.DataFrame] = None
    electricity_prices: Optional[pd.DataFrame] = None

    @classmethod
    def read_from_raw_data(
        cls,
        fossil_prices_path: Path | str,
        electricity_prices_path: Optional[Path | str] = None,
    ) -> ExoPricesReader:
        """Load exogenous price CSVs from disk.

        Args:
            fossil_prices_path: Path to fossil fuel prices CSV.
            electricity_prices_path: Path to electricity prices CSV.

        Returns:
            ExoPricesReader with loaded DataFrames (None if file absent).
        """
        if isinstance(fossil_prices_path, str):
            fossil_prices_path = Path(fossil_prices_path)
        fossil = pd.read_csv(fossil_prices_path) if fossil_prices_path.exists() else None

        elec = None
        if electricity_prices_path is not None:
            if isinstance(electricity_prices_path, str):
                electricity_prices_path = Path(electricity_prices_path)
            if electricity_prices_path.exists():
                elec = pd.read_csv(electricity_prices_path)

        return cls(fossil_prices=fossil, electricity_prices=elec)
