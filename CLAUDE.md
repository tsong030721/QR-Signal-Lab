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
  backtest/      costs.py works; engine.py has the math; pipeline.py (run_backtests) is a non-running draft -> rewrite
  evaluate/      NEW — metrics.py, split.py, sweep.py
  spec.py        StrategySpec dataclass, the unit of research  [Phase 1 done]
  run_experiment.py  NEW — single CLI entry point
```

- **`StrategySpec`** (frozen dataclass, in `spec.py`): `feature_steps` (ordered list of `(fn, params, scope)`, scope = `"series"` or `"cross_sectional"`), `input_field`, `rule_fn`, `rule_params`, `sizing`, `cost_bps`, `universe`, `date_range`; derives `.name`. `universe` defaults to `all_tickers()`, accepts a subset or `SECTORS["energy"]`. A sweep = list of specs.
- **`BacktestResult`** (dataclass, not yet built): positions, weights, gross/net returns, turnover, equity, originating spec. Metrics computed *from* this, never inside the backtest.

## Remaining phases

**Phase 2 — Finish backtest**
- `backtest/pipeline.py`: rewrite as `run_backtest(spec, panel) -> BacktestResult`. Sequence: shift → align → size → weights → turnover → costs → net → equity.
- `backtest/costs.py`: `compute_turnovers` uses `.diff()` — seed an explicit zero row so flat→first-trade isn't free turnover.
- New `backtest/sizing.py`: inverse-vol weights + portfolio vol target, using `realized_volatility` (computed, currently unused — RECS.md #8).
- Fill or delete `backtest/config.py` (currently empty).
- Assert the lag contract centrally: position at *t* uses info ≤ *t*, earns return *t*→*t+1*.

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
- **Phase 1 done**: `spec.py` (`StrategySpec`), `access/data_api.load_panel`, spec-driven `feature/pipeline.py`/`strategy/pipeline.py`. Old string-keyed `FEATURES_1D`/`FEATURE_RULES` registries deleted. Multi-feature rules (e.g. vol-filtering, which needs positions plus an auxiliary vol-regime feature) are explicitly tabled — not yet composable through a single `StrategySpec`. `notebooks/exploration.ipynb` still targets the pre-Phase-1 API — leave as-is until Phase 4.
- **Next up: Phase 2** (backtest rewrite). `qr_signal_lab/backtest/` has untracked work in progress — check `git status` before assuming Phase 2 hasn't started.
