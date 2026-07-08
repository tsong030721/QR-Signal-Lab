"""
Normalization utilities for computing cross-sectional statistics across multiple assets.

All functions operate on pandas DataFrames and return 
a DataFrame preserving the original index.
"""
import pandas as pd

def cross_sectional_rank(df: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
    """
    Compute the rank of magnitude at each timestamp, standardized to [0,1].
        [ascending]: toggle ascending/descending order of magnitude
    """
    return df.rank(axis=1, ascending=ascending, pct=True)

def cross_sectional_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the z-scores at each timestamp.
    """
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1), axis=0)
