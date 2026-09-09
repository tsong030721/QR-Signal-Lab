"""
Utilities to apply strategy to time-lagged data.
"""

import pandas as pd

from ..common.errors import SchemaMismatch

def compute_returns(exposure: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Applies time=t exposure to time=t+1 returns; caller must shift beforehand.
    `exposure` may be raw positions or gross-bounded weights - result semantics differ accordingly.
    Requires `exposure`/`returns` to share index/columns; raises SchemaMismatch otherwise.
    """
    _assert_aligned(exposure, returns)
    return exposure.mul(returns, fill_value=0.0)


def compute_portfolio_weights(positions: pd.DataFrame) -> pd.DataFrame:
    """
    Builds portfolio weights from positions. Positions must be NaN-free and aligned.
    Exposure invariant (asserted): gross exposure = 1.0 on any non-flat row, 0.0 on an all-flat row.
    """
    assert not positions.isna().any().any(), (
        "positions must not contain NaN before weighting - a NaN cell would "
        "be skipped by skipna sums below and could pass the gross-exposure "
        "assert while still surviving into the returned weights"
    )

    row_sum = positions.abs().sum(axis=1).replace(0, 1)
    weights = positions.div(row_sum, axis = 0)

    gross = weights.abs().sum(axis=1)
    flat = positions.abs().sum(axis=1) == 0
    assert (gross[~flat] - 1.0).abs().lt(1e-9).all(), "gross exposure must be 1.0 on non-flat rows"
    assert (gross[flat] == 0).all(), "gross exposure must be 0.0 on flat rows"

    return weights


def compute_gross_returns(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.Series:
    """Computes gross portfolio returns from portfolio weights (not raw positions)."""
    weighted_returns = compute_returns(weights, returns)
    gross_returns = weighted_returns.sum(axis=1)

    return gross_returns

def compute_net_returns(gross_returns: pd.Series, costs: pd.Series) -> pd.Series:
    """Computes net returns: gross returns minus transaction costs."""
    return gross_returns - costs

def compute_equity_curve(net_returns: pd.Series, initial: int) -> pd.Series:
    """Computes the equity curve by compounding net returns from `initial`."""
    return (1+net_returns).cumprod() * initial


def _assert_aligned(a: pd.DataFrame, b: pd.DataFrame) -> None:
    if not a.index.equals(b.index) or not a.columns.equals(b.columns):
        raise SchemaMismatch(
            "Index/columns mismatch between the two frames being combined - "
            "align explicitly upstream rather than relying on pandas' implicit "
            "union/broadcast, which would silently drop or zero-fill labels."
        )