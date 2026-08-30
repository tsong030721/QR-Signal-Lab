"""
Canonical return computations.

Returns are not a feature: every consumer of price data (strategy, backtest,
evaluation) must obtain returns from this module, not by re-deriving them.
Guards against non-positive prices leaking through as a >100% return or a
silent NaN from log() of a negative number - see cleaning._handle_missing,
which should already have dropped such rows upstream.
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
    """
    Single-series log return with the same non-positive-price guard as
    log_returns(). Exposed so any feature needing a log price change over an
    arbitrary window (momentum, volatility) goes through this module's
    validation rather than calling base.log_return directly and re-deriving
    the guard.
    """
    return base.log_return(base.validated_prices(series, label), periods)
