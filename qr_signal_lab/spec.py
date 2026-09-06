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
class StrategySpec:
    feature_steps: list[FeatureStep]
    input_field: str
    rule_fn: Callable
    rule_params: dict = field(default_factory=dict)
    sizing: str = "equal_weight"
    cost_bps: float = 0.0
    universe: list[str] = field(default_factory=all_tickers)
    date_range: tuple[str | None, str | None] = (None, None)

    def __post_init__(self):
        if not self.feature_steps:
            raise InvalidRequest("StrategySpec requires at least one feature step.")
        if not self.universe:
            raise InvalidRequest("StrategySpec requires a non-empty universe.")

    @property
    def name(self) -> str:
        steps = "-".join(
            f"{fn.__name__}({','.join(f'{k}={v}' for k, v in params.items())})"
            for fn, params, _ in self.feature_steps
        )
        rule = f"{self.rule_fn.__name__}({','.join(f'{k}={v}' for k, v in self.rule_params.items())})"
        return f"{steps}__{rule}__{self.sizing}__{self.cost_bps}bps"
