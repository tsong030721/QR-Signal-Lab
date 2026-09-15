"""
Runs a list of StrategySpecs end-to-end (feature -> strategy -> backtest ->
metrics) against one shared panel and reports one metrics DataFrame across
the sweep, indexed by spec.name. A sweep answers "how sensitive is this idea
to its parameters", not "which single spec had the best number" -
summarize_sharpe reports the distribution, not the max, by design.
"""
import pandas as pd

from ..backtest.pipeline import run_backtest
from ..common.errors import InvalidRequest
from ..feature.pipeline import compute_feature
from ..spec import StrategySpec
from ..strategy.pipeline import compute_position
from .metrics import compute_metrics

def run_sweep(specs: list[StrategySpec], panel: pd.DataFrame) -> pd.DataFrame:
    """
    Backtests every spec against the same panel, returns one metrics
    DataFrame: one row per spec (indexed by spec.name), one column per metric.
    Raises InvalidRequest on an empty sweep or on two distinct specs that
    stringify to the same name (a collision would silently drop a result).
    """
    if not specs:
        raise InvalidRequest("run_sweep requires at least one spec.")

    rows: dict[str, dict] = {}
    for spec in specs:
        if spec.name in rows:
            raise InvalidRequest(
                f"Duplicate spec name in sweep: {spec.name!r} - two distinct "
                "specs must not stringify identically."
            )
        features = compute_feature(spec, panel)
        positions = compute_position(spec, features)
        result = run_backtest(spec, panel, positions)
        rows[spec.name] = compute_metrics(result)

    return pd.DataFrame.from_dict(rows, orient="index")

def summarize_sharpe(sweep_metrics: pd.DataFrame) -> pd.Series:
    """
    Describes the Sharpe distribution across a sweep (count/mean/std/min/
    quartiles/max) - deliberately not just the max. The best Sharpe in a
    sweep is disproportionately likely to be a multiple-testing fluke, not
    the strongest idea; the distribution is the honest summary. describe()
    silently excludes NaN Sharpes (e.g. a spec with constant returns) from
    those stats via pandas' skipna default, so nan_count is appended
    explicitly rather than letting those specs vanish unreported.
    """
    if "sharpe" not in sweep_metrics.columns:
        raise InvalidRequest("sweep_metrics has no 'sharpe' column - was it produced by run_sweep?")
    sharpe = sweep_metrics["sharpe"]
    summary = sharpe.describe()
    summary["nan_count"] = sharpe.isna().sum()
    return summary
