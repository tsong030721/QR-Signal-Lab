"""
Low-level utilities: rolling & cumulative data, lagged returns.
Minimum periods and lagging periods are exposed.
NaN's from out-of-scope data are not truncated.
"""
import pandas as pd
import numpy as np

from ..common.errors import InvalidRequest

# ----------------------------
# Rolling
# ----------------------------
def rolling_mean(
        series: pd.Series, 
        window: int, 
        min_periods: int | None = None
    ) -> pd.Series:
    """
    Compute the rolling mean with *window*.
    """
    if min_periods is None:
        min_periods = window

    _check_window(series.size, window, min_periods)

    return series.rolling(window, min_periods).mean()


def rolling_std(
        series: pd.Series, 
        window: int, 
        min_periods: int | None = None,
        ddof: int = 0
    ) -> pd.Series:
    """
    Compute the rolling standard deviation with *window*.
    """
    if min_periods is None:
        min_periods = window

    _check_window(series.size, window, min_periods)

    return series.rolling(window, min_periods).std(ddof)


def rolling_zscore(
        series: pd.Series, 
        window: int, 
        min_periods: int | None = None, 
        ddof: int = 0
    ) -> pd.Series:
    """
    Compute the rolling mean with a given *window*.
    """
    if min_periods is None:
        min_periods = window

    _check_window(series.size, window, min_periods)
    
    rolling = series.rolling(window, min_periods)

    return (series - rolling.mean()) / rolling.std(ddof)


# ----------------------------
# Cumulative
# ----------------------------
def expanding_mean(series: pd.Series) -> pd.Series:
    return series.expanding().mean()

def expanding_std(series: pd.Series) -> pd.Series:
    return series.expanding().std()

def expanding_zscore(series: pd.Series, ddof : int = 0) -> pd.Series:
    expanding = series.expanding()

    return (series - expanding.mean()) / expanding.std(ddof)

# ----------------------------
# Returns
# ----------------------------
def lag(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Lag the data by *periods* to prevent lookahead bias.
    """
    _check_period(series.size, periods)

    return series.shift(periods)


def pct_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Percentage return: (P_t/P_{t-n}) - 1
    """
    _check_period(series.size, periods)

    return series.pct_change(periods)


def log_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Log return: log(P_t/P_{t-n})
    """
    _check_period(series.size, periods)

    return np.log(series).diff(periods)


# ----------------------------
# Helpers
# ----------------------------
def _check_window(size: int, window: int, min_periods: int) -> None:
    if window > size:
        raise InvalidRequest(f"Window ({window}) exceeds length of series ({size}).")
    if min_periods > window:
        raise InvalidRequest(f"Min_periods ({min_periods}) exceeds window ({window}).")
    
    
def _check_period(size: int, period: int) -> None:
    if period > size:
        raise InvalidRequest(f"Period ({period}) exceeds length of series ({size}).")