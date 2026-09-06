"""
Cross-sectional normalization utilities across multiple assets.
Operate on wide DataFrames, returning a DataFrame with the original index preserved.
"""
import pandas as pd

def cross_sectional_rank(df: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
    """Ranks magnitude at each timestamp, normalized to [0,1]. ascending=True: 1.0 = highest value."""
    return df.rank(axis=1, ascending=ascending, pct=True)

def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Computes the cross-sectional z-score at each timestamp."""
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
