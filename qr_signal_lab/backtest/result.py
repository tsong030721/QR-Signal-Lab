"""
BacktestResult: the output of run_backtest. Every result carries the spec
that produced it - no number without provenance.
"""
from dataclasses import dataclass

import pandas as pd

from ..spec import StrategySpec

@dataclass(frozen=True)
class BacktestResult:
    spec: StrategySpec
    positions: pd.DataFrame       # lagged, executable positions (direction, not capital)
    weights: pd.DataFrame         # sized + normalized portfolio weights (capital exposure)
    turnover: pd.Series
    gross_returns: pd.Series
    net_returns: pd.Series
    equity: pd.Series
