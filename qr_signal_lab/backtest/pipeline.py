"""
Assembles a full backtest from precomputed positions. Never computes
features or positions itself - those come from feature.pipeline/
strategy.pipeline, called by the caller before run_backtest. Fixed sequence:
shift -> align -> size -> weights -> turnover -> costs -> net -> equity.
"""
import pandas as pd

from ..common.errors import InvalidRequest, SchemaMismatch
from ..feature.returns import panel_log_returns
from ..feature.volatility import realized_volatility
from ..spec import StrategySpec
from . import config, costs, engine, sizing
from .result import BacktestResult

def run_backtest(spec: StrategySpec, panel: pd.DataFrame, positions: pd.DataFrame) -> BacktestResult:
    """
    positions: signal-time positions from strategy.pipeline.compute_position(
    spec, ...), not yet lagged - already restricted to spec.universe.
    panel: the same load_panel-shaped panel the positions were computed from;
    used here only to derive forward returns, never to recompute a feature.
    """
    lagged_positions = _lag(positions)

    prices = _slice_universe(panel[config.PRICE_FIELD], spec.universe, config.PRICE_FIELD)
    returns = _slice_universe(panel_log_returns(panel, config.PRICE_FIELD), spec.universe, config.PRICE_FIELD)
    _assert_aligned(lagged_positions, returns)

    weights = _size(spec, lagged_positions, returns, prices)

    turnover = costs.compute_turnovers(weights)
    transaction_costs = costs.transaction_costs(turnover, spec.cost_bps)

    gross_returns = engine.compute_gross_returns(weights, returns)
    net_returns = engine.compute_net_returns(gross_returns, transaction_costs)
    equity = engine.compute_equity_curve(net_returns, config.INITIAL_CAPITAL)

    return BacktestResult(
        spec=spec,
        positions=lagged_positions,
        weights=weights,
        turnover=turnover,
        gross_returns=gross_returns,
        net_returns=net_returns,
        equity=equity,
    )

def _lag(positions: pd.DataFrame) -> pd.DataFrame:
    """
    The single, explicit shift enforcing the lag contract: a position decided
    using info through t can only earn the return from t to t+1. This is the
    only place positions are ever shifted - no other layer may re-shift them.
    """
    assert not positions.isna().any().any(), (
        "positions must not contain NaN before lagging - strategy rules "
        "must map every undefined signal to flat before returning positions"
    )

    lagged = positions.shift(1).fillna(0.0)  # row 0's shift-induced NaN only: no prior day exists, so flat
    assert (lagged.iloc[0] == 0).all(), "lag contract violated: row 0 must be flat - no prior-day info exists"
    return lagged

def _slice_universe(field_panel: pd.DataFrame, universe: list[str], field: str) -> pd.DataFrame:
    missing = set(universe) - set(field_panel.columns)
    if missing:
        raise InvalidRequest(f"Universe tickers missing from panel field {field!r}: {sorted(missing)}")
    return field_panel[universe]

def _assert_aligned(positions: pd.DataFrame, returns: pd.DataFrame) -> None:
    if not positions.index.equals(returns.index) or not positions.columns.equals(returns.columns):
        raise SchemaMismatch(
            "Index/columns mismatch between positions and returns - align "
            "explicitly upstream rather than relying on pandas' implicit "
            "union/fill, which would silently drop or zero-fill labels."
        )

def _size(spec: StrategySpec, positions: pd.DataFrame, returns: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Applies spec.sizing to produce gross-normalized weights, then spec.vol_target's optional overlay on top."""
    if spec.sizing == "equal_weight":
        weights = engine.compute_portfolio_weights(positions)
    else:
        vol = prices.apply(lambda col: realized_volatility(col, spec.vol_window), axis=0)
        weights = sizing.inverse_vol_weights(positions, vol)

    if spec.vol_target is not None:
        base_returns = engine.compute_gross_returns(weights, returns)
        weights = sizing.vol_target_scale(weights, base_returns, spec.vol_target, spec.vol_window)

    return weights
