"""
Stable API to retrieve cleaned data.
"""
import pandas as pd
from datetime import datetime

from qr_signal_lab.common.config import CLEAN_DIR

from ..common import paths
from ..common.errors import InvalidRequest

# ----------------------------
# Public API
# ----------------------------
def load(symbol: str, *, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """
    Loads cleaned DataFrame from CLEAN_DIR with option to slice by date range.
    """
    # Validate path and load data
    path = paths.clean_path(symbol)
    if not paths.valid_file(path):
        raise InvalidRequest(f"Cleaned data for {symbol} not found.")
    
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise Exception(f"Failed to load data for {symbol}: {e}")

    # Verify date range is valid
    start, end = _check_dates(start, end, symbol, df)

    # Slice by date range
    df = df.loc[start:end]

    return df

# ----------------------------
# Helpers
# ----------------------------
def _check_dates(start: str | None, end: str | None, symbol: str, df: pd.DataFrame) -> datetime:
    min_date, max_date = df.index.min(), df.index.max()
    start = min_date if start is None else max(_parse_date(start), min_date)
    end = max_date if end is None else min(_parse_date(end), max_date)

    if start > max_date:
        raise InvalidRequest(f"Start date {start} is after max date {max_date} for {symbol}.")
    if end < min_date:
        raise InvalidRequest(f"End date {end} is before min date {min_date} for {symbol}.")
    if start > end:
        raise InvalidRequest(f"Start date {start} is after end date {end} for {symbol}.")
    
    return start, end


def _parse_date(date: str) -> datetime:
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
        return dt
    except ValueError as e:
        raise InvalidRequest(f"Wrong date format: {date}. Expected YYYY-MM-DD.") from e