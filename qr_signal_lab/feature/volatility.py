"""
Volatility statistics and regime utilities.
Operate on pandas Series, returning aligned Series with the original index preserved.
"""
import math
import pandas as pd
import numpy as np
from .base import rolling_std
from .returns import log_return_series

# Declared periods-per-year assumption for annualization - trading days, not
# calendar days. Any caller annualizing vol/Sharpe/etc. elsewhere should use
# this rather than a bare literal.
TRADING_DAYS_PER_YEAR = 252

def realized_volatility(
        series: pd.Series,
        window: int,
        annualized: bool = False
    ) -> pd.Series:
    """Rolling standard deviation of log returns. annualized=True scales by sqrt(TRADING_DAYS_PER_YEAR)."""
    volatility = rolling_std(log_return_series(series, series.name or "realized_volatility input"), window)
    if annualized:
        volatility *= math.sqrt(TRADING_DAYS_PER_YEAR)

    return volatility


def vol_regime_flag(
        series: pd.Series,
        short_window: int,
        long_window: int | None = None
    ) -> pd.Series:
    """
    Flags whether short-term realized vol exceeds long-term: 1 = high-vol, 0 = calm.
    NaN = unknown (insufficient history) - callers must treat NaN as high-vol, not calm.
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