"""
Apply signal-to-position mappings for computed features.

Each function takes a DataFrame of feature values and returns a DataFrame of positions
with values in {-1, 0, 1} - corresponding to short, flat, long, respectively - with
dimensions preserved. Sign convention: +1 = long. NaN feature values always map to
flat (0), never to a directional bet.
"""
import numpy as np
import pandas as pd

from ..common.errors import SchemaMismatch

def momentum_positions(
        momentum: pd.DataFrame,
        criteria: float | None = 0
    ) -> pd.DataFrame:
    """
    Long when momentum > criteria, short when momentum < criteria, flat on NaN or a
    tie with criteria.
        [momentum]: Wide dataframe with time series momentum data of multiple tickers.
        [criteria]: Borderline value for determining long/short.
    """
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
    Long the top of the cross-sectional ranking, short the bottom, flat on NaN.
    Assumes `pct_rank` is ascending: 1.0 = highest value of the underlying feature,
    0.0 = lowest (see feature.normalization.cross_sectional_rank).
        [pct_rank]: Wide dataframe of ticker rankings normalized to [0,1].
        [top_pct]: Percentile at/above which tickers are long (e.g. 0.8 = top 20%).
        [bottom_pct]: Percentile at/below which tickers are short (e.g. 0.2 = bottom 20%).
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
    Deactivate positions where the volatility regime is high or unknown.
        [positions]: Computed short/long/flat positions.
        [vol_flag]: Corresponding DataFrame of volatility flags (1 = high-vol,
                    0 = calm, NaN = unknown - treated as high-vol, not calm).
    """
    if not positions.index.equals(vol_flag.index) or not positions.columns.equals(vol_flag.columns):
        raise SchemaMismatch(
            "Index/columns mismatch between positions and vol_flag - align "
            "explicitly upstream rather than relying on pandas' implicit "
            "union/fill, which would silently drop or zero-fill labels."
        )

    keep = 1 - vol_flag.fillna(1)

    return positions.mul(keep)