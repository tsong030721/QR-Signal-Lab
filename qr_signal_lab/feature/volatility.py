"""
Compute volatility in the desired time window.
   - Compute volatility comparisons and trends
"""
import math
import pandas as pd
import numpy as np
from .base import rolling_std, log_return

def realized_volatility(
        series: pd.Series,
        window: int,
        annualized: bool = False
    ):
    """
    Compute rolling sdev on log returns
    [series]     : Price data for asset
    [window]     : Length of sliding window
    [annualized] : Option to extrapolate annualized values
    """
    volatility = rolling_std(log_return(series), window)
    if annualized:
        volatility *= math.sqrt(252)
    
    return volatility


def vol_regime_flag(
        series: pd.Series,
        short_window: int = 20,
        long_window: int = 100
    ):
    """
    Determine whether short term volatility exceeds long term
    [series]       : Price data for asset
    [short_window] : Length of short-term window
    [long_windwow] : Length of long-term window
    Flagged as 0 or 1
    """
    short_vol = realized_volatility(series, short_window)
    long_vol = realized_volatility(series, long_window)
    flag = (short_vol > long_vol).astype(int)
    flag[(short_vol.isna()) | (long_vol.isna())] = np.nan

    return flag

def atr():
    pass