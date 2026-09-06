"""
Runs a StrategySpec's rule against a computed feature DataFrame.
"""
import pandas as pd

from ..spec import StrategySpec

def compute_position(spec: StrategySpec, feature_df: pd.DataFrame) -> pd.DataFrame:
    """Applies spec.rule_fn to feature_df, returning positions in {-1, 0, 1}."""
    return spec.rule_fn(feature_df, **spec.rule_params)
