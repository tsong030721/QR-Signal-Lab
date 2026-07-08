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
    Determine whether short term volatility exceeds long term,
    flagged as 0/1
    """
    if long_window is None:
        long_window = 5 * short_window
        
    short_vol = realized_volatility(series, short_window)
    long_vol = realized_volatility(series, long_window)
    flag = (short_vol > long_vol).astype(int)
    flag[(short_vol.isna()) | (long_vol.isna())] = np.nan

    return flag

def atr():
    pass