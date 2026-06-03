"""
Cross-sectional normalization tools for multiple assets.
   - Standardize scale across assets
   - How strong is this signal relative to others?
"""
import pandas as pd

def cross_sectional_rank(df: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
    """
    Rank by value at each timestamp, standardized to [0,1]
    [df]       : Arbitrary feature value accross multiple assets, indexed by timestamp.
    [ascending]: Ascending/descending order
    """
    return df.rank(axis=1, ascending=ascending, pct=True)

def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    [df]: Arbitrary feature value accross multiple assets, indexed by timestamp.
    """
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
