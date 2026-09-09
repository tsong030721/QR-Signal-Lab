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

@dataclass(frozen=True)
class StrategySpec:
    features: dict[str, FeatureSpec]
    rule_steps: list[RuleStep]
    sizing: str = "equal_weight"
    cost_bps: float = 0.0
    universe: list[str] = field(default_factory=all_tickers)
    date_range: tuple[str | None, str | None] = (None, None)

    def __post_init__(self):
        if not self.features:
            raise InvalidRequest("StrategySpec requires at least one named feature.")
        if not self.rule_steps:
            raise InvalidRequest("StrategySpec requires at least one rule step.")
        if not self.universe:
            raise InvalidRequest("StrategySpec requires a non-empty universe.")

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
        return f"{features}__{rules}__{self.sizing}__{self.cost_bps}bps"

def _steps_str(steps: list[FeatureStep]) -> str:
    return "-".join(f"{fn.__name__}({_params_str(params)})" for fn, params, _ in steps)

def _params_str(params: dict) -> str:
    return ",".join(f"{k}={v}" for k, v in params.items())
