"""
Utility to collectively apply feature computations for ticker data.
"""
import pandas as pd
from .config import FEATURES_1D, FEATURES_2D

def compute_features(
        data: dict[str, pd.DataFrame], 
        normalize: bool | None = False
    ) -> dict[str, pd.DataFrame]:
    """Computes all features in config.FEATURES_1D, one wide DataFrame (tickers as columns) per feature."""
    features = dict()
    # Populate features with empty dataframes
    for label in FEATURES_1D:
        columns = dict()

        # Create wide dataframe
        for ticker in data:
            window = FEATURES_1D[label]["window"]
            if window:
                columns[ticker] = FEATURES_1D[label]["method"](data[ticker]["close"], window)
            else:
                columns[ticker] = FEATURES_1D[label]["method"](data[ticker]["close"])
        features[label] = pd.DataFrame(columns)

        # Normalize if indicated and applicable
        if normalize and FEATURES_1D[label]["normalize"]:
            for normalizer in FEATURES_2D:
                label_csec = label + "_" + normalizer
                features[label_csec] = FEATURES_2D[normalizer]["method"](features[label])
    
    return features