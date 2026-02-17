"""
Path-related helper functions.
"""
from pathlib import Path

from . import config

def valid_file(path: Path) -> bool:
    return path.exists() and path.is_file()

def get_symbols() -> list[str]:
    symbols = [p.stem for p in config.RAW_DIR.glob("*.parquet")]
    return symbols

def clean_path(symbol: str) -> Path:
    out_path = config.CLEAN_DIR / f"{symbol}.parquet"
    return out_path

def raw_path(symbol: str) -> Path:
    out_path = config.RAW_DIR / f"{symbol}.parquet"
    return out_path