from .rules import momentum_positions, csec_rank_positions, vol_filtered_positions

FEATURE_RULES = {
            "momentum_return": {
                "method": momentum_positions
                },
            "momentum_return_rank": {
                "method": csec_rank_positions
                }
        }

FILTER_RULES = {
            "volatility": {
                "method": vol_filtered_positions
                }
        }