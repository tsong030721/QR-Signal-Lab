"""
Cross-sectional normalization utilities across multiple assets.
Operate on wide DataFrames, returning a DataFrame with the original index preserved.
"""
import pandas as pd

from ..common.universe import sector_of

def cross_sectional_rank(df: pd.DataFrame, ascending: bool = True, within_sector: bool = True) -> pd.DataFrame:
    """
    Ranks magnitude at each timestamp, normalized to [0,1]. ascending=True: 1.0
    = highest value. within_sector=True (default): rank each sector's tickers
    only against each other, not the full universe - pass False explicitly to
    rank across every column regardless of sector.
    """
    if not within_sector:
        return df.rank(axis=1, ascending=ascending, pct=True)

    return _apply_within_sector(df, lambda group: group.rank(axis=1, ascending=ascending, pct=True))

def cross_sectional_zscore(df: pd.DataFrame, within_sector: bool = True) -> pd.DataFrame:
    """
    Computes the cross-sectional z-score at each timestamp. within_sector=True
    (default): z-score each sector's tickers only against each other, not the
    full universe - pass False explicitly to z-score across every column
    regardless of sector.
    """
    if not within_sector:
        return _zscore(df)

    return _apply_within_sector(df, _zscore)

def _zscore(df: pd.DataFrame) -> pd.DataFrame:
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)

def _apply_within_sector(df: pd.DataFrame, fn) -> pd.DataFrame:
    """Groups df's columns by sector, applies fn to each sector's sub-frame independently, reassembles in original column order."""
    sectors: dict[str, list[str]] = {}
    for ticker in df.columns:
        sectors.setdefault(sector_of(ticker), []).append(ticker)

    parts = [fn(df[tickers]) for tickers in sectors.values()]
    return pd.concat(parts, axis=1)[df.columns]
