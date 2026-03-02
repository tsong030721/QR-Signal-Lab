"""
Single asset time-series momentum features.
Momentum is the recent directional persistence in returns.
Helps to answer: how like is it that the recent trend continues?
"""
import pandas as pd

from . import base
from ..common.errors import InvalidRequest

def momentum_return(series: pd.Series, periods: int) -> pd.Series:
    """
    Compute momentum of returns: P_t/P_{t-n} - 1
    """
    return base.pct_return(series, periods)


def ma_ratio(series: pd.Series, window: int) -> pd.Series:
    """
    Computes ratio of return to moving average: P_t/(MA_t) - 1
    """
    ma = base.rolling_mean(series, window)
    return series / ma - 1


def ema_diff(series: pd.Series, span: int) -> pd.Series:
    """
    Computes difference from exponential moving average: P_t - EMA_t
    EMA is defined recursively EMA_t = aP_t + (1-a)EMA_{t-1}; smooth price trend
    By default, a = 2/(n+1) where n := span.
    """
    ema = series.ewm(span=span, adjust=False).mean()
    return series - ema