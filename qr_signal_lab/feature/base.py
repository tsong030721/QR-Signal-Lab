"""
Low-level feature utilities - atomic, reusable transformations.
"""
import pandas as pd

from ..common.errors import InvalidRequest

def lag(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Lag the data by *periods* to prevent lookahead bias.
    """
    if periods >= series.size:
        raise InvalidRequest(f"Lagging period ({periods}) is at least the length of series ({series.size}).")
    
    return series.shift(periods)

# ----------------------------
# Rolling
# ----------------------------
def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    """
    Compute the rolling mean with a given window size.
    """
    if window > series.size:
        raise InvalidRequest(f"Window ({window}) is greater than the length of series ({series.size}).")
    
    return series.rolling(window=window).mean()

def rolling_std(series: pd.Series, window: int) -> pd.Series:
    """
    Compute the rolling standard deviation with a given window size.
    """
    if window > series.size:
        raise InvalidRequest(f"Window ({window}) is greater than the length of series ({series.size}).")
    
    return series.rolling(window=window).std()

def rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    """
    Compute the rolling mean with a given window size.
    """
    if window > series.size:
        raise InvalidRequest(f"Window ({window}) is greater than the length of series ({series.size}).")
    
    rolling = series.rolling(window=window)
    zscore = (rolling - rolling.mean()) / rolling.std()

    return zscore

# ----------------------------
# Returns
# ----------------------------
def pct_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Percentage return: (P_t/P_{t-n}) - 1
    """
    pass

def log_return(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Log return: log(P_t/P_{t-n})
    """
    pass