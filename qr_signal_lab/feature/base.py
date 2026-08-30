"""
Foundational utilities for computing rolling statistics and returns.

All functions operate on pandas Series and return aligned Series
preserving the original index. 
"""
import pandas as pd
import numpy as np

from ..common.errors import InvalidRequest, DataValidationError

# ----------------------------
# Validation
# ----------------------------
def validated_prices(series: pd.Series, label: str) -> pd.Series:
    """
    Guard shared by every return-like computation (feature.returns, and any
    feature - e.g. momentum - built directly on log/pct price changes): a
    non-positive price makes P_t/P_{t-n} undefined and must fail loudly
    rather than silently produce an inf/NaN/garbage value downstream.
    """
    if (series <= 0).any():
        raise DataValidationError(
            f"Non-positive price for {label}; return-like computations are undefined. "
            "Re-run cleaning to drop invalid rows before computing returns."
        )
    return series

# ----------------------------
# Rolling
# ----------------------------
def rolling_mean(
        series: pd.Series, 
        window: int, 
        min_periods: int | None = None
    ) -> pd.Series:
    """
    Compute the rolling mean of a time series.
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
    Compute the rolling standard deviation of a time series.
        [ddof]: degrees of freedom for std computation
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
    Compute the rolling z-score of a time series.
        [ddof]: degrees of freedom for std computation
    """
    if min_periods is None:
        min_periods = window

    _check_window(series.size, window, min_periods)
    
    rolling = series.rolling(window, min_periods)

    return (series - rolling.mean()) / rolling.std(ddof)

# ----------------------------
# Returns
# ----------------------------
def lag(series: pd.Series, periods: int = 1) -> pd.Series:
    _check_period(series.size, periods)

    return series.shift(periods)


def pct_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Compute the percentage returns of a time series: (P_t/P_{t-n})-1
    """
    _check_period(series.size, periods)

    return series.pct_change(periods)


def log_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Compute the log returns of a time series: log(P_t/P_{t-n})
    """
    _check_period(series.size, periods)

    return np.log(series / lag(series, periods))


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