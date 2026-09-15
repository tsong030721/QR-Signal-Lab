"""
Fixed in-sample/out-of-sample boundary, declared once here so every notebook
and sweep evaluates against the same split instead of each re-deriving its
own cutoff. split_result() partitions an already-run BacktestResult in two -
it never re-runs a backtest or touches a signal, it only slices dates.
"""
import pandas as pd

from ..backtest import config, engine
from ..backtest.result import BacktestResult
from ..common.errors import InvalidRequest

# IS = [start, IS_OOS_BOUNDARY), OOS = [IS_OOS_BOUNDARY, end]. 2019-01-01
# leaves ~6 years OOS (through a covid crash and a rate-hike regime) against
# ~12-18 years IS depending on a ticker's start - a deliberate, fixed choice,
# not swept or tuned per spec.
IS_OOS_BOUNDARY = "2019-01-01"

def split_result(result: BacktestResult, boundary: str = IS_OOS_BOUNDARY) -> tuple[BacktestResult, BacktestResult]:
    """
    Splits result into (is_result, oos_result) at `boundary` (inclusive on
    the OOS side). Each side's equity curve is recompounded from
    backtest.config.INITIAL_CAPITAL independently via backtest.engine's
    single equity-curve function, so each is self-contained and directly
    readable ("OOS equity" = growth of $INITIAL_CAPITAL invested at the
    boundary), not a discontinuous slice of the full-sample curve.
    """
    index = result.net_returns.index
    try:
        boundary_ts = pd.Timestamp(boundary)
    except (ValueError, TypeError) as e:
        raise InvalidRequest(f"Invalid IS/OOS boundary {boundary!r}: {e}") from e
    if not (index.min() < boundary_ts < index.max()):
        raise InvalidRequest(
            f"IS/OOS boundary {boundary} must fall strictly within the result's "
            f"date range [{index.min().date()}, {index.max().date()}]."
        )

    is_mask = pd.Series(index < boundary_ts, index=index)
    return _slice_result(result, is_mask), _slice_result(result, ~is_mask)

def _slice_result(result: BacktestResult, mask: pd.Series) -> BacktestResult:
    net_returns = result.net_returns.loc[mask]
    return BacktestResult(
        spec=result.spec,
        positions=result.positions.loc[mask],
        weights=result.weights.loc[mask],
        turnover=result.turnover.loc[mask],
        gross_returns=result.gross_returns.loc[mask],
        net_returns=net_returns,
        equity=engine.compute_equity_curve(net_returns, config.INITIAL_CAPITAL),
    )
