"""
Functions to fetch OHLCV data (single/batch) as DataFrames for ticker(s).
"""
import yfinance as yf
import pandas as pd
from datetime import datetime
from .config import PERIODS, INTERVALS
from ..common.errors import InvalidRequest, DataSourceError, EmptyData

# ----------------------------
# Public API
# ----------------------------
def fetch_one(symbol: str, *, start: str | None = None, end: str | None = None,
              period: str | None = None, interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV for a single ticker. Returns a DataFrame or raises.
    """
    # Validate symbol and params
    symbol = _clean_symbols([symbol])
    _validate_params(start, end, period, interval)

    return _yfdownload_wrapper(symbol, start, end, period, interval)


def fetch_batch(symbols: list[str], *, start: str | None = None, end: str | None = None,
                period: str | None = None, interval: str = "1d") -> pd.DataFrame:
    """
    Fetch merged OHLCV for multiple tickers with MultiIndex columns. 
    Returns a DataFrame or raises.
    """
    # Validate symbols and params
    symbols = _clean_symbols(symbols)
    _validate_params(start, end, period, interval)

    return _yfdownload_wrapper(symbols, start, end, period, interval)


def fetch_batch_separate(symbols: list[str], start: str | None = None, end: str | None = None,
                         period: str | None = None, interval: str = "1d") -> list[pd.DataFrame]:
    """
    Fetches a separate OHLCV for each of the multiple tickers. 
    Returns a list of DataFrames or raises.
    """
    # Validate symbols and parameters
    symbols = _clean_symbols(symbols)
    _validate_params(start, end, period, interval)

    # Iteratively call yf download
    df = []
    for s in symbols:
        df.append(_yfdownload_wrapper([s], start, end, period, interval))

    return df

# ----------------------------
# Helpers
# ----------------------------
def _yfdownload_wrapper(symbols: list[str], start: str | None, end: str | None,
                        period: str | None, interval: str) -> list[pd.DataFrame]:
    """
    Wrapper for calling download from yahoo finance.
    Returns the relavent DataFrame or raises.
    """
    # Call yf download
    df = yf.download(symbols, start=start, end=end, 
                     period=period, interval=interval,
                     auto_adjust=False, progress=False)
    
    # Validate result
    if df is None:
        msg = f"{symbols[0]}." if len(symbols) == 1 else f"{len(symbols)} symbols."
        raise DataSourceError("yfinance returned None for " + msg)
    if df.empty:
        msg = f"{symbols[0]}." if len(symbols) == 1 else f"{len(symbols)} symbols."
        raise EmptyData("No data for " + msg + f" (start:{start}, end:{end}, period:{period}, interval:{interval})")

    return df


def _validate_params(start: str | None, end: str | None, 
                 period: str | None, interval: str | None
    ) -> None:
    """
    Validate fetch parameters.
    """
    # Validate period
    if period is not None and period not in PERIODS:
        raise InvalidRequest("Invalid value for period.")
    
    # Validate interval
    if interval is not None and interval not in INTERVALS:
        raise InvalidRequest("Invalid value for interval.")
    
    # Mutual exclusivity
    if period is not None and (start is not None and end is not None):
        raise InvalidRequest("Specify either period OR start & end, not both.")

    # Validate dates
    start = None if start is None else _parse_date(start)
    end = None if end is None else _parse_date(end)
    if start is not None and end is not None:
        if start >= end:
            raise InvalidRequest("Start date must precede end date.")

def _clean_symbols(symbols: list[str]) -> list[str]:
    cleaned = []
    for s in symbols:
        s.strip()
        if not s:
            raise InvalidRequest("Symbol must be a non-empty string.")
        cleaned.append(s)
    return cleaned


def _parse_date(date: str) -> datetime:
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        return dt
    except ValueError as e:
        raise InvalidRequest(f"Wrong date format: {date}. Expected YYYY-MM-DD.") from e