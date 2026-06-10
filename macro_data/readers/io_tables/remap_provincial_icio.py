"""
Remap the provincial ICIO table from hybrid industry codes to the canonical
50-sector disaggregated classification.

The original ``icio_2014_can_provinces.csv`` uses a mix of aggregated (A, D, J)
and disaggregated (B05a/b/c, C10T12…C31T33) codes.  This script splits those
aggregated rows/columns using output-share ratios from the national
disaggregated ICIO table (``sectoral_disagg_CAN_2014_v2.csv``).

Output: ``raw_data/icio/icio_2014_can_provinces_remapped.csv``
— drop-in replacement for the existing provincial reader path.

Usage:  uv run python macro_data/readers/io_tables/remap_provincial_icio.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ── constants ──────────────────────────────────────────────────────────
# Aggregate → sub-sector mapping (from oecd_econ/mappings.json + manual
# electricity split based on the national disaggregated table).
SPLIT_MAP: dict[str, list[str]] = {
    "A": ["A01", "A03"],
    "D": ["D01a", "D01b", "D01c", "D01d", "D01e"],
    "J": ["J58T60", "J61", "J62"],
}

# Industries that are already at the right granularity — pass through.
KEEP_CODES = {
    "B05a", "B05b", "B05c", "B07", "B09",
    "C10T12", "C13T15", "C16", "C17", "C19", "C20", "C21", "C22", "C23",
    "C24a", "C24b", "C25", "C26", "C27", "C28", "C29", "C30", "C31T33",
    "E", "F", "G",
    "H49", "H50", "H51", "H52", "H53",
    "I", "K", "L", "M", "N", "O", "P", "Q", "R_S",
}

# Industries that appear only in the national disaggregated table but are
# produced by splitting in the provincial table (i.e., they appear as
# sub-sectors of the aggregated codes above).
SPLIT_SUB_CODES = {
    code for sub_list in SPLIT_MAP.values() for code in sub_list
}

# All production industries in the target (canonical) classification.
TARGET_PRODUCTION_CODES = sorted(KEEP_CODES | SPLIT_SUB_CODES)

# Special row / column labels (non-industry entries).
SPECIAL_ROW_CODES = {"Value Added", "Taxes Less Subsidies", "Output",
                     "Intermediate Inputs"}
SPECIAL_COL_CODES = {"Fixed Capital Formation", "Government Consumption",
                     "Household Consumption", "Output"}


# ── helpers ─────────────────────────────────────────────────────────────

def load_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load both the national and provincial ICIO tables."""
    raw = REPO_ROOT / "raw_data" / "icio"
    nat = pd.read_csv(
        raw / "sectoral_disagg_CAN_2014_v2.csv", header=[0, 1], index_col=[0, 1],
    )
    prov = pd.read_csv(
        raw / "icio_2014_can_provinces.csv", header=[0, 1], index_col=[0, 1],
    )
    return nat, prov


def compute_split_shares(nat: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Compute output-share ratios for splitting aggregated codes.

    Returns ``{agg: {sub1: share, sub2: share}}`` where shares sum to 1.
    """
    out = nat.loc[("TOTAL", "Output")]  # Series indexed by (country, industry)

    shares: dict[str, dict[str, float]] = {}
    for agg, subs in SPLIT_MAP.items():
        # Use TOTAL-level columns (the national ICIO has a TOTAL country column
        # group for combined output).
        vals = {}
        for sub in subs:
            col_candidates = [c for c in nat.columns if c[1] == sub]
            if col_candidates:
                vals[sub] = float(out[col_candidates[0]])
            else:
                vals[sub] = 0.0
        total = sum(vals.values())
        if total > 0:
            shares[agg] = {s: v / total for s, v in vals.items()}
        else:
            # Equal split fallback (shouldn't happen with real data).
            n = len(subs)
            shares[agg] = {s: 1.0 / n for s in subs}
    return shares


def get_province_entities(df: pd.DataFrame) -> list[str]:
    """Return the list of province/country entities in the provincial table."""
    provinces = set(df.index.get_level_values(0))
    provinces.discard("TOTAL")
    provinces.discard("ROW")
    return sorted(provinces)


def _row_industries(df: pd.DataFrame) -> set[str]:
    """Return the set of industry codes in row index level 1."""
    return set(df.index.get_level_values(1)) - SPECIAL_ROW_CODES


def _col_industries(df: pd.DataFrame) -> set[str]:
    """Return the set of industry codes in column index level 1."""
    return set(df.columns.get_level_values(1)) - SPECIAL_COL_CODES


def split_dimension(
    df: pd.DataFrame,
    shares: dict[str, dict[str, float]],
    axis: str = "rows",
) -> pd.DataFrame:
    """Split aggregated industry codes in either rows or columns.

    Parameters
    ----------
    df : pd.DataFrame
        Provincial ICIO table.
    shares : dict
        Split shares from ``compute_split_shares``.
    axis : {"rows", "cols"}
        Which dimension to split.

    Returns
    -------
    pd.DataFrame
        Table with aggregate codes replaced by their sub-sector splits.
    """
    if axis == "rows":
        # Work with index = (entity, industry)
        entities = sorted(set(df.index.get_level_values(0)) - {"TOTAL", "ROW"})
        # Build new data: list of (index_tuple, series) → concat
        pieces: list[pd.Series] = []
        new_index_entries: list[tuple[str, str]] = []

        for idx in df.index:
            entity, ind = idx
            if entity == "TOTAL":
                continue  # handled later
            if ind in SPLIT_MAP:
                row_data = df.loc[idx]
                for sub, share in shares[ind].items():
                    pieces.append(row_data * share)
                    new_index_entries.append((entity, sub))
            else:
                pieces.append(df.loc[idx])
                new_index_entries.append(idx)

        # Rebuild index: re-index with the new multi-index
        result = pd.DataFrame(
            {tuple(new_index_entries[i]): pieces[i] for i in range(len(pieces))}
        ).T
        result.index = pd.MultiIndex.from_tuples(result.index)

        # Append TOTAL rows
        for total_idx in df.loc["TOTAL"].index:
            result.loc[("TOTAL", total_idx), :] = df.loc[("TOTAL", total_idx)]

        result = result.sort_index()
        return result

    else:  # axis == "cols"
        result = df.copy()
        new_columns: dict[tuple[str, str], pd.Series] = {}
        cols_to_drop: list[tuple[str, str]] = []

        for col in result.columns:
            entity, ind = col
            if ind in SPLIT_MAP:
                col_data = result[col]
                for sub, share in shares[ind].items():
                    new_columns[(entity, sub)] = col_data * share
                cols_to_drop.append(col)

        result = result.drop(columns=cols_to_drop)
        for new_col, data in new_columns.items():
            result[new_col] = data

        # Re-sort columns
        result = result.reindex(sorted(result.columns), axis=1)
        return result


# ── main ────────────────────────────────────────────────────────────────

def main() -> None:
    nat, prov = load_tables()

    shares = compute_split_shares(nat)
    print("Split shares:")
    for agg, subs in shares.items():
        print(f"  {agg}: {subs}")

    provinces = get_province_entities(prov)
    print(f"\nProvinces found: {provinces}")

    # ── 1. Split rows ──
    print("\nSplitting rows …")
    remapped = split_dimension(prov, shares, axis="rows")

    # ── 2. Split columns ──
    print("Splitting columns …")
    remapped = split_dimension(remapped, shares, axis="cols")

    # ── 3. Verify no aggregate codes remain ──
    row_inds = _row_industries(remapped)
    col_inds = _col_industries(remapped)
    remaining_agg = (row_inds | col_inds) & set(SPLIT_MAP.keys())
    if remaining_agg:
        print(f"\n⚠️  WARNING: Aggregate codes remain: {remaining_agg}")
    else:
        print("\n✅ No aggregate codes remain after splitting.")

    # ── 4. Check completeness ──
    target = set(TARGET_PRODUCTION_CODES)
    missing_rows = target - row_inds
    missing_cols = target - col_inds
    if missing_rows:
        print(f"⚠️  Missing row industries: {sorted(missing_rows)}")
    else:
        print(f"✅ All {len(target)} target industries present in rows.")
    if missing_cols:
        print(f"⚠️  Missing column industries: {sorted(missing_cols)}")
    else:
        print(f"✅ All {len(target)} target industries present in columns.")

    # ── 5. Fix scaling ──
    # The provincial ICIO has values in thousands/millions (raw).
    # The reader multiplies by 1e6 on load (line 329 of default_readers.py).
    # The national table has much larger values.
    # We DON'T rescale here — the reader will multiply by 1e6.

    # ── 6. Save ──
    out_path = REPO_ROOT / "raw_data" / "icio" / "icio_2014_can_provinces_remapped.csv"
    remapped.to_csv(out_path)
    print(f"\n✅ Saved to: {out_path}")
    print(f"   Shape: {remapped.shape}")
    print(f"   Row entities: {sorted(remapped.index.get_level_values(0).unique())}")
    print(f"   Column entities: {sorted(remapped.columns.get_level_values(0).unique())}")


if __name__ == "__main__":
    main()
