"""
Performance metrics computed from a BacktestResult. Metrics never recompute
a signal or a return - they consume net_returns/turnover/equity exactly as
the backtest layer produced them. Each metric is a standalone function over
plain Series so it can be hand-verified against a known return series
independently of the rest of the pipeline; compute_metrics() is the
aggregator that pulls fields off a BacktestResult and calls each one. Every
public function validates its own input (non-empty, NaN-free) rather than
relying on a caller upstream to have done so - these are meant to be called
directly in tests, not only through compute_metrics.
"""
import math

import pandas as pd

from ..backtest.result import BacktestResult
from ..common.errors import InvalidRequest
from ..feature.volatility import TRADING_DAYS_PER_YEAR

def annualized_return(returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """
    Compounded annualized return: (prod(1+r))^(periods_per_year/n) - 1. NaN
    (not a complex number) if cumulative growth is non-positive - a >100%
    cumulative loss makes CAGR undefined, and Python's ** on a negative base
    with a fractional exponent would otherwise silently return a complex
    number (RECS.md #1: extreme single-day prints are real, not theoretical).
    """
    _require_valid(returns, "returns")
    n = len(returns)
    growth = (1.0 + returns).prod()
    if growth <= 0:
        return float("nan")
    return growth ** (periods_per_year / n) - 1.0

def annualized_volatility(returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Annualized volatility: std(r) * sqrt(periods_per_year). ddof=0, matching feature/base.py's rolling_std default."""
    _require_valid(returns, "returns")
    return returns.std(ddof=0) * math.sqrt(periods_per_year)

def sharpe_ratio(returns: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """
    Annualized Sharpe: mean(r) * periods_per_year / annualized_volatility(r).
    No risk-free adjustment (not tracked anywhere in this codebase, so
    returns are treated as excess returns as-is). NaN if returns are
    constant (vol=0) - undefined, not zero.
    """
    vol = annualized_volatility(returns, periods_per_year)
    if vol == 0:
        return float("nan")
    return returns.mean() * periods_per_year / vol

def max_drawdown(equity: pd.Series) -> float:
    """
    Max peak-to-trough drawdown as a fraction: <= 0, 0 = equity never fell
    below its running peak. -0.23 means a 23% drawdown from peak.
    """
    _require_valid(equity, "equity")
    drawdown = equity / equity.cummax() - 1.0
    return drawdown.min()

def calmar_ratio(returns: pd.Series, equity: pd.Series, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> float:
    """Calmar: annualized return / |max drawdown|. NaN if there was never a drawdown (undefined, not infinite)."""
    mdd = max_drawdown(equity)
    if mdd == 0:
        return float("nan")
    return annualized_return(returns, periods_per_year) / abs(mdd)

def hit_rate(returns: pd.Series) -> float:
    """Fraction of days with strictly positive net return. Flat (zero-return) days count against the hit rate, not for it."""
    _require_valid(returns, "returns")
    return (returns > 0).mean()

def avg_turnover(turnover: pd.Series) -> float:
    """Mean per-day turnover, in the same units costs.compute_turnovers produces (sum of |weight changes|)."""
    _require_valid(turnover, "turnover")
    return turnover.mean()

def t_stat(returns: pd.Series) -> float:
    """t-stat on the null that mean daily return is 0: mean / (std / sqrt(n)), ddof=1 (sample std, standard for a t-test). NaN if n<2 or std=0."""
    _require_valid(returns, "returns")
    n = len(returns)
    if n < 2:
        return float("nan")
    std = returns.std(ddof=1)
    if std == 0:
        return float("nan")
    return returns.mean() / (std / math.sqrt(n))

def compute_metrics(result: BacktestResult, periods_per_year: int = TRADING_DAYS_PER_YEAR) -> dict:
    """
    One metrics dict for a single BacktestResult, keyed by metric name plus
    spec_name for standalone provenance (also the key sweep.run_sweep indexes
    a multi-spec metrics DataFrame by).
    """
    returns = result.net_returns
    return {
        "spec_name": result.spec.name,
        "n_days": len(returns),
        "ann_return": annualized_return(returns, periods_per_year),
        "ann_vol": annualized_volatility(returns, periods_per_year),
        "sharpe": sharpe_ratio(returns, periods_per_year),
        "max_drawdown": max_drawdown(result.equity),
        "calmar": calmar_ratio(returns, result.equity, periods_per_year),
        "hit_rate": hit_rate(returns),
        "avg_turnover": avg_turnover(result.turnover),
        "t_stat": t_stat(returns),
    }

def top_contributors(result: BacktestResult, n: int = 10) -> pd.DataFrame:
    """
    The N biggest-magnitude single-day net-return days, ranked by |net_return|
    descending. Non-negotiable before trusting any spec's Sharpe (RECS.md #3:
    a result where a handful of days explain the whole edge is a data
    artifact, not a signal). share_of_total_return is a simple linear share
    (net_return / sum(net_returns)) for concentration diagnostics only - it
    ignores compounding, so it is not a P&L attribution.
    """
    if n <= 0:
        raise InvalidRequest(f"n must be positive, got {n}.")
    returns = result.net_returns
    _require_valid(returns, "net_returns")

    ranked_index = returns.abs().sort_values(ascending=False).index
    top = returns.reindex(ranked_index).iloc[:min(n, len(returns))]

    total = returns.sum()
    share = top / total if total != 0 else pd.Series(float("nan"), index=top.index)

    return pd.DataFrame({"net_return": top, "share_of_total_return": share})

def _require_valid(series: pd.Series, label: str) -> None:
    if len(series) == 0:
        raise InvalidRequest(f"{label} is empty - cannot compute a metric over zero observations.")
    if series.isna().any():
        raise InvalidRequest(f"{label} contains NaN - metrics never interpret missing data implicitly (see CLAUDE.md's NaN convention).")
