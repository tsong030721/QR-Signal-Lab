"""
Canonical return computations - the sole source of returns for all downstream layers.
Raises on non-positive prices instead of emitting a silent bad return.
"""
import pandas as pd

from . import base

def simple_returns(data: dict[str, pd.DataFrame], field: str = "close") -> pd.DataFrame:
    """
    Wide DataFrame (tickers as columns) of simple returns: P_t/P_{t-1} - 1.
    """
    return pd.DataFrame({
        ticker: base.pct_return(base.validated_prices(df[field], ticker))
        for ticker, df in data.items()
    })

def log_returns(data: dict[str, pd.DataFrame], field: str = "close") -> pd.DataFrame:
    """
    Wide DataFrame (tickers as columns) of log returns: log(P_t / P_{t-1}).
    """
    return pd.DataFrame({
        ticker: log_return_series(df[field], ticker)
        for ticker, df in data.items()
    })

def log_return_series(series: pd.Series, label: str, periods: int = 1) -> pd.Series:
    """Single-series log return with the same non-positive-price guard as log_returns()."""
    return base.log_return(base.validated_prices(series, label), periods)

def panel_log_returns(panel: pd.DataFrame, field: str) -> pd.DataFrame:
    """
    Wide log returns (tickers as columns) from a load_panel-shaped panel
    (MultiIndex (field, ticker) columns) - the load_panel-native counterpart
    to log_returns(), which expects the older dict[ticker, DataFrame] shape.
    """
    prices = panel[field]
    return prices.apply(lambda col: log_return_series(col, col.name), axis=0)
