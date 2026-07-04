"""
Momentum utilities for computing directional persistence and adjusted returns.

All functions operate on pandas Series and return aligned Series
preserving the original index. 
"""
import pandas as pd

from . import base

def momentum_return(series: pd.Series, window: int) -> pd.Series:
    """
    Compute the momentum of returns (log) of a time series.
    """
    return base.log_return(series, window)


def ma_ratio(series: pd.Series, window: int) -> pd.Series:
    """
    Computes the ratio of returns to the moving average: P_t/(MA_t)-1
    """
    ma = base.rolling_mean(series, window)
    return series / ma - 1


def ema_diff(series: pd.Series, span: int) -> pd.Series:
    """
    Compute the difference of returns from exponential moving average: P_t-EMA_t
    EMA (EMA_t = aP_t + (1-a)EMA_{t-1}) provides a smoothened price trend.
    """
    ema = series.ewm(span=span, adjust=False).mean()
    return series - ema