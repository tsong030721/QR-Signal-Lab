# CLAUDE.md

## What this is

Personal quant-research sandbox: commodity futures (daily, yfinance, 2001→present). Pipeline: ingest → clean → feature → strategy → backtest → evaluate (evaluate doesn't exist yet — this refactor builds it).

Universe: 19 tickers / 4 sectors in `common/universe.py` (`SECTORS`, `all_tickers()`, `sector_of()`). Not a fixed size — edit that file to add/remove symbols; `ingestion/config.TICKERS = all_tickers()`. Tickers have ragged history (e.g. `BZ=F` starts 2007) — tolerate leading NaN per ticker, never assume a common start date.

`docs/v0.md`/`v1.md`: superseded, historical only. `RECS.md`: past mistakes + fixes — read once, don't re-derive.

## Commands

```
pip install -r requirements.txt
python3 -m qr_signal_lab.ingestion.run_ingestion -v   # -> data/raw/{sym}.parquet
python3 -m qr_signal_lab.cleaning.run_clean -v        # -> data/clean/{sym}.parquet
```
No tests/linter/build yet (Phase 4). No feature/strategy/backtest entry point yet (Phase 4 adds `run_experiment.py`) — drive manually per `notebooks/exploration.ipynb`.

## V1 target architecture

```
qr_signal_lab/
  common/        config, paths, errors, logging, types      [unchanged]
  ingestion/                                                  [unchanged]
  cleaning/                                                   [Phase 0 done]
  access/        load() single-symbol + load_panel(symbols, start, end) -> MultiIndex (field, ticker) columns  [Phase 1 done]
  feature/       spec-driven; params live on the spec, not a global registry  [Phase 1 done]
  strategy/      NaN-safe rules; dispatch off spec, not string matching  [Phase 1 done]
  backtest/      run_backtest(spec, panel, positions) -> BacktestResult  [Phase 2 done]
  evaluate/      NEW — metrics.py, split.py, sweep.py
  spec.py        StrategySpec dataclass, the unit of research  [Phase 1 + 2 done]
  run_experiment.py  NEW — single CLI entry point
```

- **`StrategySpec`** (frozen dataclass, in `spec.py`): `features` (`dict[str, FeatureSpec]`, each a named `input_field` + ordered `(fn, params, scope)` step chain, scope = `"series"` or `"cross_sectional"`), `rule_steps` (ordered `(fn, params, feature_name)`; the first step's fn takes just its named feature, every later step folds in one more named feature on top of the running positions — this is how multi-feature rules like vol-filtering compose), `sizing` (`"equal_weight"` or `"inverse_vol"`), `vol_window`, `vol_target` (optional annualized vol-targeting overlay), `cost_bps`, `universe`, `date_range`; derives `.name`. `universe` defaults to `all_tickers()`, accepts a subset or `SECTORS["energy"]` — `feature/pipeline.py` restricts every named feature to it before running its steps, so cross-sectional steps rank over the declared universe and every feature ends up column-aligned with every other. A sweep = list of specs.
- **`BacktestResult`** (frozen dataclass, in `backtest/result.py`): `spec`, `positions` (lagged), `weights`, `turnover`, `gross_returns`, `net_returns`, `equity`. Metrics computed *from* this, never inside the backtest.

## Remaining phases

**Phase 3 — Evaluation**
- `evaluate/metrics.py`: Sharpe, ann. return/vol, max drawdown, Calmar, hit rate, avg turnover, t-stat on mean daily return.
- `evaluate/split.py`: fixed IS/OOS boundary, declared once.
- `evaluate/sweep.py`: list of specs → metrics DataFrame keyed by spec name. Report Sharpe *distribution*, not the max.
- **Top-contributor report on every result** (N biggest single-day P&L days) — non-negotiable before trusting any new spec's numbers.

**Phase 4 — Entry point, tests, docs**
- `run_experiment.py`: `python3 -m qr_signal_lab.run_experiment --spec <name>` → `results/{spec_name}/{metrics.json, equity.parquet, spec.json}`.
- `tests/`: fixtures with known answers (monotonic price → +1 momentum; NaN column → 0 position; hand-computed Sharpe on a known return series). Pin `requirements.txt`; add `pytest`.
- Rewrite `README.md`: overview, data-discipline caveat up front, install, commands, one worked example, repo layout.
- Thin `notebooks/exploration.ipynb` to a consumer of `run_experiment` — no pipeline logic in notebooks.

## Conventions to hold throughout

- I/O only in `ingestion`/`cleaning`/`access`. Transform layers preserve index/column semantics unless their contract explicitly states otherwise.
- Wide DataFrames, dates as index, tickers as columns, from the feature layer on.
- Returns come from `feature/returns.py` only — never re-derived elsewhere.
- NaN is never interpreted implicitly. Features may contain NaN when undefined; strategy rules explicitly map NaN to positions, normally flat. No NaN survives into executable positions/weights.
- Every rule states its sign convention (`+1 = long`); check against a monotonic-input case before trusting it.
- A strategy is a `StrategySpec` value, not a set of matching string keys.
- Raise typed errors from `common/errors.py` at the point of failure; catch only at layer boundaries.
- Every result carries the spec that produced it — no number without provenance.
- Before trusting a good Sharpe: check the top P&L contributors. A great-looking result is a bug report until attribution is checked.
- No implicit lookahead. A value computed using information through t may only
  affect returns after its declared execution time. Any shift happens exactly
  once, at an explicit layer boundary.
- All cross-layer pandas operations require explicit index/column alignment.
  Never rely on accidental broadcasting or silent label dropping.
- Positions and portfolio weights are distinct concepts. Positions express
  direction/signal; weights express capital exposure. Functions must state
  which they consume and produce.
- Portfolio-weight functions state their exposure invariant explicitly
  (e.g. gross exposure = 1, net exposure unconstrained). Assert it where practical.
- Turnover is computed from changes in executable portfolio weights, not raw
  signals/positions, unless explicitly documented otherwise.
- Transaction costs are expressed in bps and converted exactly once.
  Cost assumptions belong in the backtest specification, never as hidden constants.
- Return timing and frequency are explicit. Never annualize Sharpe, volatility,
  or other metrics without a declared periods-per-year assumption.
- Avoid fillna/dropna as cleanup operations. Missing-data handling must encode
  an intentional financial meaning.
- Research parameters are configuration/spec values, never buried as magic
  constants inside implementation code.
- Tests prioritize invariants over example outputs: no-lookahead, alignment,
  sign, exposure, turnover, NaN handling, and deterministic results.

## Status

- **Phase 0 done**: price-validity guard, dedupe fix, typed errors, NaN-safe strategy rules, correct rank/vol-regime sign conventions. Detail: RECS.md #1, #5, #6.
- **Convention audit done**: two-pass (build + independent strict review) fixed gaps against the conventions above — returns routed through `feature/returns.py` everywhere, NaN-free assertion before weighting, explicit alignment guards, turnover's flat-prior seed, typed errors on I/O failures. Detail: RECS.md #10, #11.
- **Phase 1 done**: `spec.py` (`StrategySpec`, `FeatureSpec`), `access/data_api.load_panel`, spec-driven `feature/pipeline.py`/`strategy/pipeline.py`. Old string-keyed `FEATURES_1D`/`FEATURE_RULES` registries deleted. Multi-feature rules (e.g. vol-filtering) are supported via named `features` + a `rule_steps` chain — no changes needed to existing rule_fns (`momentum_positions`, `csec_rank_positions`, `vol_filtered_positions`) since they already matched the chain's two call shapes. `notebooks/exploration.ipynb` still targets the pre-Phase-1 API — leave as-is until Phase 4.
- **Phase 2 done**: `backtest/pipeline.run_backtest(spec, panel, positions) -> BacktestResult` — positions/features are always computed by the caller (`feature.pipeline`/`strategy.pipeline`) before calling this; `run_backtest` only does shift → align → size → weights → turnover → costs → net → equity, never recomputes a signal. `_lag` is the sole `.shift(1)` call site and asserts row 0 is flat (the lag-contract check). New `backtest/sizing.py` (`inverse_vol_weights`, `vol_target_scale`, both built on `feature/volatility.py`) and `backtest/result.py` (`BacktestResult`). `feature/volatility.py` gained `return_volatility` (rolling std of an already-computed return series) since `realized_volatility` needs strictly-positive prices and can't take a portfolio return stream directly — `vol_target_scale` needed this and originally called `realized_volatility` by mistake, caught by a smoke test. `feature/returns.py` gained `panel_log_returns` (the `load_panel`-shaped counterpart to `log_returns`'s older per-symbol-dict input). `feature/normalization.py`'s rank/zscore now default `within_sector=True` (`sector_of`-grouped), with `within_sector=False` as the explicit opt-out. `backtest/config.py` now holds `INITIAL_CAPITAL`/`PRICE_FIELD`. `StrategySpec`/`BacktestResult` stay out of `common/` — `common/` is domain-agnostic infra (paths/logging/errors/config), and both are domain models with a natural producer (`spec.py` itself; `backtest/pipeline.py` for the result).
- **Phase 3 done**: `evaluate/metrics.py` (`annualized_return`, `annualized_volatility`, `sharpe_ratio`, `max_drawdown`, `calmar_ratio`, `hit_rate`, `avg_turnover`, `t_stat`, `compute_metrics`, `top_contributors`) — every public function validates its own input (non-empty, NaN-free, raising `InvalidRequest`) rather than trusting a caller to have done so, since these are meant to be hand-verified directly against known return series in Phase 4's tests, not only reached through `compute_metrics`. `annualized_return` returns NaN rather than a complex number on non-positive cumulative growth (Python's `**` on a negative base with a fractional exponent would otherwise silently succeed). `evaluate/split.py`: `IS_OOS_BOUNDARY = "2019-01-01"`, declared once; `split_result` partitions an already-run `BacktestResult` by date mask (never re-runs a backtest), recompounding each half's equity independently from `backtest.config.INITIAL_CAPITAL` via `backtest.engine.compute_equity_curve` so IS/OOS equity curves are each self-contained. `evaluate/sweep.py`: `run_sweep(specs, panel) -> DataFrame` wires feature → strategy → backtest → metrics per spec, indexed by `spec.name`, raising on duplicate names; `summarize_sharpe` reports the Sharpe distribution (`.describe()` plus an explicit `nan_count`, since `.describe()` silently drops NaN) rather than the max, per CLAUDE.md's explicit instruction against reporting best-of-sweep. Reviewed by an independent subagent for modularity/correctness (verdict: approve with nits, all addressed before commit).
- **Next up: Phase 4** (entry point, tests, docs).
