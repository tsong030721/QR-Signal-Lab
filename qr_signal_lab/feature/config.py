from .base import rolling_mean, rolling_std, rolling_zscore
from .momentum import momentum_return, ma_ratio, ema_diff
from .normalization import cross_sectional_rank, cross_sectional_zscore
from .volatility import realized_volatility, vol_regime_flag

FEATURES_1D = {
                "mean": {
                    "method": rolling_mean,
                    "class": "base",
                    "window": 20,
                    "normalize": False
                    }, 
                "std": {
                    "method": rolling_std,
                    "class": "base",
                    "window": 20,
                    "normalize": False
                    }, 
                "zscore": {
                    "method": rolling_zscore,
                    "class": "base",
                    "window": 20,
                    "normalize": False
                    }, 
                "momentum_return": {
                    "method": momentum_return,
                    "class": "momentum",
                    "window": 20,
                    "normalize": True
                    },
                "ma_ratio": {
                    "method": ma_ratio,
                    "class": "momentum",
                    "window": 20,
                    "normalize": True
                    }, 
                "ema_diff": {
                    "method": ema_diff,
                    "class": "momentum",
                    "window": 20,
                    "normalize": False
                    },
                "realized_volatility": {
                    "method": realized_volatility,
                    "class": "volatility",
                    "window": 20,
                    "normalize": False
                    }, 
                "vol_regime_flag": {
                    "method": vol_regime_flag,
                    "class": "volatility",
                    "window": 20,
                    "normalize": False
                    }
           }

FEATURES_2D = {
                "rank": {
                    "method": cross_sectional_rank,
                    "class": "normalization",
                    "window": None
                    }, 
                "zscore": {
                    "method": cross_sectional_zscore,
                    "class": "normalization",
                    "window": None
                    }
            }