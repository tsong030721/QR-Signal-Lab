"""
Runs a StrategySpec's feature chain against a loaded panel.
"""
import pandas as pd

from ..common.errors import InvalidRequest
from ..spec import StrategySpec

def compute_feature(spec: StrategySpec, panel: pd.DataFrame) -> pd.DataFrame:
    """Applies spec.feature_steps in order to panel[spec.input_field], returning the final wide DataFrame."""
    result = panel[spec.input_field]
    for fn, params, scope in spec.feature_steps:
        if scope == "series":
            result = result.apply(lambda col: fn(col, **params), axis=0)
        elif scope == "cross_sectional":
            result = fn(result, **params)
        else:
            raise InvalidRequest(f"Unknown feature-step scope: {scope!r}")
    return result
