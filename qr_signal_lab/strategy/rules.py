"""
Apply signal-to-position mappings for computed features.

Each function takes a DataFrame of feature values and returns
a DataFrame of values in {-1,0,1} - corresponding to short, flat,
long, respectively - with dimensions preserved.
"""
import pandas as pd

def momentum_positions(
        momentum: pd.DataFrame,
        criteria: int | None = 0
    ) -> pd.DataFrame:
    """
    Compute signal (long, short) based on time series momentum.
        [momentum]: Wide dataframe with time series momentum data of
            multiple tickers.
        [criteria]: Borderline value for determining long/short.
    """
    def convert(x):
        return 1 if x > criteria else -1

    return momentum.map(convert)

def csec_rank_positions(
        pct_rank: pd.DataFrame,
        top_pct: float | None = 0.2,
        bottom_pct: float | None = 0.8
    ) -> pd.DataFrame:
    """
    Compute signal (long, short) based on ranking across tickers.
        [pct_rank]: Wide data frame with ticker rankings normalized to [0,1]
        [top_pct]: Top percentile value of tickers to long.
        [bottom_pct]: Bottom percentile value of tickers to short.
    """
    def convert(x):
        if x < top_pct:
            return 1
        elif x > bottom_pct:
            return -1
        else:
            return 0
        
    return pct_rank.map(convert)

def vol_filtered_positions(
        positions: pd.DataFrame,
        vol_flag: pd.DataFrame
    ) -> pd.DataFrame:
    """
    Deactivate positions that have a volatility flag.
        [positions]: Computed short/long/flat positions.
        [vol_flag]: Corresponding df of volatility flags.
    """
    filter = 1 - vol_flag

    return positions.mul(filter, fill_value=0)