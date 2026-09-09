"""
Runs a StrategySpec's rule chain against computed named features.
"""
import pandas as pd

from ..spec import StrategySpec

def compute_position(spec: StrategySpec, features: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Applies spec.rule_steps in order, returning positions in {-1, 0, 1}.
    The first step's fn consumes only its named feature: fn(feature_df, **params)
    -> positions. Every later step folds in one more named feature on top of
    the running positions: fn(positions, feature_df, **params) -> positions.
    """
    positions = None
    for fn, params, feature_name in spec.rule_steps:
        feature_df = features[feature_name]
        positions = fn(feature_df, **params) if positions is None else fn(positions, feature_df, **params)
    return positions
