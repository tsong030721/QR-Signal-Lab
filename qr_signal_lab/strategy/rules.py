"""
Signal-to-position mapping rules.
Output positions are in {-1, 0, 1} (short/flat/long), dimensions preserved; +1 = long.
NaN feature values always map to flat (0), never a directional bet.
"""
import numpy as np
import pandas as pd

from ..common.errors import SchemaMismatch

def momentum_positions(
        momentum: pd.DataFrame,
        criteria: float | None = 0
    ) -> pd.DataFrame:
    """Long when momentum > criteria, short when < criteria, flat on NaN or a tie. +1 = long."""
    values = np.select(
        [momentum > criteria, momentum < criteria],
        [1, -1],
        default=0,
    )
    return pd.DataFrame(values, index=momentum.index, columns=momentum.columns)

def csec_rank_positions(
        pct_rank: pd.DataFrame,
        top_pct: float | None = 0.8,
        bottom_pct: float | None = 0.2
    ) -> pd.DataFrame:
    """
    Long the top of the cross-sectional ranking, short the bottom, flat on NaN. +1 = long.
    Assumes `pct_rank` ascending: 1.0 = highest value, 0.0 = lowest.
    """
    values = np.select(
        [pct_rank >= top_pct, pct_rank <= bottom_pct],
        [1, -1],
        default=0,
    )
    return pd.DataFrame(values, index=pct_rank.index, columns=pct_rank.columns)

def vol_filtered_positions(
        positions: pd.DataFrame,
        vol_flag: pd.DataFrame
    ) -> pd.DataFrame:
    """
    Zeroes out positions where volatility regime is high or unknown.
    vol_flag: 1 = high-vol, 0 = calm, NaN = unknown - treated as high-vol.
    """
    if not positions.index.equals(vol_flag.index) or not positions.columns.equals(vol_flag.columns):
        raise SchemaMismatch(
            "Index/columns mismatch between positions and vol_flag - align "
            "explicitly upstream rather than relying on pandas' implicit "
            "union/fill, which would silently drop or zero-fill labels."
        )

    keep = 1 - vol_flag.fillna(1)

    return positions.mul(keep)