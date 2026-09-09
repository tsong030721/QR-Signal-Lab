"""
Computations necessary for trading activity and cost calculations.
"""

import pandas as pd

def compute_turnovers(portfolio: pd.DataFrame) -> pd.Series:
    """
    Computes per-timestep turnover from executable portfolio weights (not raw positions).
    Prior state before row 0 is seeded flat, so the first flat->trade transition counts as real turnover.
    """
    prior = portfolio.shift(1).fillna(0.0)
    differences = (portfolio - prior).abs()
    turnovers = differences.sum(axis=1)

    return turnovers

def transaction_costs(turnovers: pd.Series, rate: float) -> pd.Series:
    """Computes transaction costs from turnovers. `rate` is in bps."""
    return turnovers * (rate / 10000)
