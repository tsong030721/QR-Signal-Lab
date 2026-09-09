"""
StrategySpec: the declarative unit of research. Holds direct references to
feature/rule functions and their params instead of string-keyed registries.
"""
from dataclasses import dataclass, field
from typing import Callable, Literal

from .common.errors import InvalidRequest
from .common.universe import all_tickers

# (function, params, scope) - scope "series" applies fn per-ticker column,
# "cross_sectional" applies fn to the whole wide frame at once.
FeatureStep = tuple[Callable, dict, Literal["series", "cross_sectional"]]

@dataclass(frozen=True)
class FeatureSpec:
    """One named feature: which panel field it reads, and its step chain."""
    input_field: str
    steps: list[FeatureStep]

    def __post_init__(self):
        if not self.steps:
            raise InvalidRequest("FeatureSpec requires at least one step.")

# (function, params, feature_name) - feature_name selects the entry of
# StrategySpec.features this rule step consumes. The first rule step's fn has
# signature fn(feature_df, **params) -> positions; every later step's fn has
# signature fn(positions, feature_df, **params) -> positions, folding in one
# more named feature on top of the running positions (e.g. a vol-regime
# filter on top of rank-based positions). This mirrors FeatureStep's chain
# shape so multi-feature rules compose the same way multi-step feature
# chains already do, and existing single-feature rule_fns (momentum_positions,
# csec_rank_positions) need no signature changes to serve as a first step.
RuleStep = tuple[Callable, dict, str]

SIZING_METHODS = {"equal_weight", "inverse_vol"}

@dataclass(frozen=True)
class StrategySpec:
    features: dict[str, FeatureSpec]
    rule_steps: list[RuleStep]
    sizing: str = "equal_weight"
    cost_bps: float = 0.0
    universe: list[str] = field(default_factory=all_tickers)
    date_range: tuple[str | None, str | None] = (None, None)
    # Rolling lookback (trading days) for inverse_vol sizing and, if set, the
    # trailing window vol_target measures realized portfolio vol over.
    vol_window: int = 20
    # Annualized target portfolio vol (e.g. 0.10 = 10%) for the vol-targeting
    # overlay applied on top of sizing; None = no vol targeting.
    vol_target: float | None = None

    def __post_init__(self):
        if not self.features:
            raise InvalidRequest("StrategySpec requires at least one named feature.")
        if not self.rule_steps:
            raise InvalidRequest("StrategySpec requires at least one rule step.")
        if not self.universe:
            raise InvalidRequest("StrategySpec requires a non-empty universe.")
        if self.sizing not in SIZING_METHODS:
            raise InvalidRequest(f"Unknown sizing method {self.sizing!r}; expected one of {sorted(SIZING_METHODS)}.")
        if self.vol_window <= 0:
            raise InvalidRequest(f"vol_window must be positive, got {self.vol_window}.")
        if self.vol_target is not None and self.vol_target <= 0:
            raise InvalidRequest(f"vol_target must be positive, got {self.vol_target}.")

        unknown = {feature_name for _, _, feature_name in self.rule_steps} - self.features.keys()
        if unknown:
            raise InvalidRequest(f"rule_steps reference features not in spec.features: {sorted(unknown)}")

    @property
    def name(self) -> str:
        features = "-".join(
            f"{feature_name}:{_steps_str(feature_spec.steps)}"
            for feature_name, feature_spec in self.features.items()
        )
        rules = "-".join(
            f"{fn.__name__}({_params_str(params)})<-{feature_name}"
            for fn, params, feature_name in self.rule_steps
        )
        vol_target = f"__vt{self.vol_target}" if self.vol_target is not None else ""
        return f"{features}__{rules}__{self.sizing}(vol_window={self.vol_window}){vol_target}__{self.cost_bps}bps"

def _steps_str(steps: list[FeatureStep]) -> str:
    return "-".join(f"{fn.__name__}({_params_str(params)})" for fn, params, _ in steps)

def _params_str(params: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in params.items())
