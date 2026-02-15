"""
Path-related helper functions.
"""
from pathlib import Path

from . import config

def clean_path(symbol: str) -> Path:
    out_path = config.CLEAN_DIR / f"{symbol}.parquet"
    return out_path

def raw_path(symbol: str) -> Path:
    out_path = config.RAW_DIR / f"{symbol}.parquet"
    return out_path