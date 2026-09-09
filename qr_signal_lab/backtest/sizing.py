"""
Portfolio sizing: inverse-vol weighting and portfolio-level vol targeting.
Both consume already-lagged, executable positions/weights - no shifting
happens here; that's asserted once, upstream, in backtest/pipeline.py.
"""
import pandas as pd

from ..common.errors import SchemaMismatch
from ..feature.volatility import return_volatility

def inverse_vol_weights(positions: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
    """
    Scales each position by 1/vol before gross-normalizing to 1.0, so each
    position contributes roughly equal risk rather than equal capital.
    vol: per-ticker realized volatility, aligned to positions.
    NaN or non-positive vol (insufficient history) makes a position
    unscalable - it is zeroed (flat), never inflated toward infinity or left
    unscaled. Exposure invariant (asserted): gross exposure = 1.0 on any
    non-flat row, 0.0 on an all-flat row - identical to
    engine.compute_portfolio_weights.
    """
    if not positions.index.equals(vol.index) or not positions.columns.equals(vol.columns):
        raise SchemaMismatch(
            "Index/columns mismatch between positions and vol - align "
            "explicitly upstream rather than relying on pandas' implicit "
            "union/fill, which would silently drop or zero-fill labels."
        )

    safe_vol = vol.where(vol > 0)
    raw = positions.div(safe_vol).fillna(0.0)

    gross = raw.abs().sum(axis=1).replace(0, 1)
    weights = raw.div(gross, axis=0)

    flat = positions.abs().sum(axis=1) == 0
    assert (weights.abs().sum(axis=1)[~flat] - 1.0).abs().lt(1e-9).all(), "gross exposure must be 1.0 on non-flat rows"
    assert (weights.abs().sum(axis=1)[flat] == 0).all(), "gross exposure must be 0.0 on flat rows"

    return weights

def vol_target_scale(weights: pd.DataFrame, portfolio_returns: pd.Series, target: float, window: int) -> pd.DataFrame:
    """
    Scales weights so trailing realized portfolio vol (annualized) tracks
    `target`: leverage_t = target / realized_vol_t, applied multiplicatively
    to weights_t. realized_vol_t uses only returns through t, so leverage_t
    is known at the same decision time as weights_t - no lookahead.
    Insufficient warmup history (realized vol undefined) -> leverage 1.0,
    i.e. the overlay is a no-op until it has enough history to compute,
    rather than fabricating a flat or full-risk default.
    """
    realized = return_volatility(portfolio_returns, window, annualized=True)
    leverage = (target / realized).fillna(1.0)
    return weights.mul(leverage, axis=0)
