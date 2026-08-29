"""
Volatility utilities for computing volatility statistics and trends.

All functions operate on pandas Series and return aligned Series
preserving the original index. 
"""
import math
import pandas as pd
import numpy as np
from .base import rolling_std, log_return

def realized_volatility(
        series: pd.Series,
        window: int,
        annualized: bool = False
    ) -> pd.Series:
    """
    Compute the rolling standard deviation on log returns
        [annualized] : Option to extrapolate annualized values
    """
    volatility = rolling_std(log_return(series), window)
    if annualized:
        volatility *= math.sqrt(252)
    
    return volatility


def vol_regime_flag(
        series: pd.Series,
        short_window: int,
        long_window: int | None = None
    ) -> pd.Series:
    """
    Flag whether short-term realized volatility exceeds long-term:
    1 = high-vol regime, 0 = calm, NaN = unknown (insufficient history).
    NaN is NOT calm - callers must treat it as high-vol / do-not-trade
    (see strategy.rules.vol_filtered_positions).
    """
    if long_window is None:
        long_window = 5 * short_window

    short_vol = realized_volatility(series, short_window)
    long_vol = realized_volatility(series, long_window)

    known = short_vol.notna() & long_vol.notna()
    flag = pd.Series(np.nan, index=series.index)
    flag[known] = (short_vol[known] > long_vol[known]).astype(int)

    return flag

def atr():
    pass