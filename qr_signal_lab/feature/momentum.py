"""
Momentum utilities for directional persistence and price-trend deviation.
Operate on pandas Series, returning aligned Series with the original index preserved.
"""
import pandas as pd

from . import base
from .returns import log_return_series

def momentum_return(series: pd.Series, window: int) -> pd.Series:
    """Computes log-return momentum of a time series over `window` periods."""
    return log_return_series(series, series.name or "momentum_return input", window)


def ma_ratio(series: pd.Series, window: int) -> pd.Series:
    """Computes the ratio of price to its moving average: P_t/MA_t - 1."""
    ma = base.rolling_mean(series, window)
    return series / ma - 1


def ema_diff(series: pd.Series, span: int) -> pd.Series:
    """Computes price minus its exponential moving average: P_t - EMA_t."""
    ema = series.ewm(span=span, adjust=False).mean()
    return series - ema