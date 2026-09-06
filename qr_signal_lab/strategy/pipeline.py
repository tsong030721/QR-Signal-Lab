"""
Utility to apply appropriate rules on feature matrices to compute positions.
"""
import pandas as pd
from .config import FEATURE_RULES, FILTER_RULES
from ..common.errors import InvalidRequest

def compute_positions(
        features: dict[str, pd.DataFrame],
        volatility: bool | None = False
    ) -> dict[str, pd.DataFrame]: 
    """Computes positions from feature values, optionally applying the volatility filter. Dimensions preserved."""
    positions = dict()
    for feature in FEATURE_RULES:
        if feature not in features:
            raise InvalidRequest(f"Label {feature} does not exist in provided features.")

        positions[feature] = FEATURE_RULES[feature]["method"](features[feature])

        if volatility:
            label = feature + "_volfilter"
            positions[label] = FILTER_RULES["volatility"]["method"](
                positions[feature], 
                features["vol_regime_flag"],
            )
    
    return positions
