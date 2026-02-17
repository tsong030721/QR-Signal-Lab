"""
Functions to standardize raw parquet data files.

"""
import pandas as pd
from . import config
from ..common import paths

# ----------------------------
# Public API
# ----------------------------
def clean_one(symbol: str) -> pd.DataFrame:
    path = paths.raw_path(symbol)
    if not paths.valid_file(path):
        raise Exception(f"Invalid path for {symbol}.")
    
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise Exception(f"Error while reading from {path}: {e}.")
    
    df = _standardize_columns(df)
    df = _enforce_types(df)
    df = _sort_and_dedupe(df)
    df= _handle_missing(df)

    return df

def clean_many(symbols: list[str]) -> list[pd.DataFrame]:
    df = [clean_one(symbol) for symbol in symbols]

    return df

# ----------------------------
# Helpers
# ----------------------------
def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flatten columns, standardize names (lowercase, no space), and remove decor.
    """
    # Flatten columns
    df.columns = df.columns.get_level_values(0)

    # Rename columns
    update = dict()
    for col in df.columns:
        update[col] = col.lower().replace(' ', '_')
    df = df.rename(columns=update)

    # Remove names
    df.index.name = None
    df.columns.name = None
    
    return df

def _enforce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce dtypes based on config.
    """
    df = df.astype(config.DTYPES, errors='raise')
    df.index = pd.to_datetime(df.index)

    return df

def _sort_and_dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort and deduplicate dataframe.
    """
    if not df.index.is_unique:
        df = df[df.index.duplicated(keep='first')]
    
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()

    return df

def _handle_missing(df: pd.DataFrame) -> pd.DataFrame:

    return df