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
from ..common.errors import DataValidationError

def simple_returns(data: dict[str, pd.DataFrame], field: str = "close") -> pd.DataFrame:
    """
    Wide DataFrame (tickers as columns) of simple returns: P_t/P_{t-1} - 1.
    """
    return pd.DataFrame({
        ticker: base.pct_return(_validated_prices(df[field], ticker))
        for ticker, df in data.items()
    })

def log_returns(data: dict[str, pd.DataFrame], field: str = "close") -> pd.DataFrame:
    """
    Wide DataFrame (tickers as columns) of log returns: log(P_t / P_{t-1}).
    """
    return pd.DataFrame({
        ticker: base.log_return(_validated_prices(df[field], ticker))
        for ticker, df in data.items()
    })

def _validated_prices(prices: pd.Series, ticker: str) -> pd.Series:
    if (prices <= 0).any():
        raise DataValidationError(
            f"Non-positive price for {ticker}; returns are undefined. "
            "Re-run cleaning to drop invalid rows before computing returns."
        )
    return prices
