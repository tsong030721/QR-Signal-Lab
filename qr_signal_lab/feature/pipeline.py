"""
Runs a StrategySpec's feature chains against a loaded panel.
"""
import pandas as pd

from ..common.errors import InvalidRequest
from ..spec import FeatureSpec, StrategySpec

def compute_feature(spec: StrategySpec, panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Computes every named feature in spec.features against panel, keyed by
    feature name. Every feature is restricted to spec.universe before its
    step chain runs, so a cross-sectional step ranks/scores over exactly the
    declared universe, and every named feature ends up on the same column
    set as every other - required for multi-feature rule steps to align.
    """
    return {name: _run_steps(feature_spec, panel, spec.universe) for name, feature_spec in spec.features.items()}

def _run_steps(feature_spec: FeatureSpec, panel: pd.DataFrame, universe: list[str]) -> pd.DataFrame:
    field_panel = panel[feature_spec.input_field]
    missing = set(universe) - set(field_panel.columns)
    if missing:
        raise InvalidRequest(
            f"Universe tickers missing from panel field {feature_spec.input_field!r}: {sorted(missing)}"
        )

    result = field_panel[universe]
    for fn, params, scope in feature_spec.steps:
        if scope == "series":
            result = result.apply(lambda col: fn(col, **params), axis=0)
        elif scope == "cross_sectional":
            result = fn(result, **params)
        else:
            raise InvalidRequest(f"Unknown feature-step scope: {scope!r}")
    return result
