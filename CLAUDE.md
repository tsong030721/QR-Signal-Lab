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

## Status: Phase 0 DONE

- Price-validity guard: `cleaning/clean_commodities.py._handle_missing` drops any row with non-positive OHLC/adj_close, logs loudly.
- Dedupe bug fixed (`~duplicated`); bare `Exception` → typed errors (`DataValidationError`/`DataSourceError`).
- `feature/returns.py` is the sole source of returns (`simple_returns`/`log_returns`), raises `DataValidationError` on non-positive price as defense-in-depth. `pct_return`/`log_return` removed from `FEATURES_1D` — returns aren't a feature.
- `strategy/rules.py`: NaN-safe (NaN → flat, never a direction); rank direction fixed (`csec_rank_positions`: `top_pct=0.8`→long, `bottom_pct=0.2`→short, ascending rank, 1.0=highest).
- `feature/volatility.vol_regime_flag` returns NaN (not 0) when unknown; `vol_filtered_positions` treats NaN as high-vol via `.fillna(1)`.
- Verification + incident detail: RECS.md #1, #5, #6.

## Status: convention audit DONE (post-expansion of "Conventions to hold throughout")

Two-pass check (build/fix agent, then an independent strict-review agent) against every bullet below, human-verified before commit. Findings and fixes:

- `feature/returns.py` is now the single source of log-return math end-to-end: added `log_return_series` (single-series, windowed); `feature/momentum.momentum_return` and `feature/volatility.realized_volatility` route through it instead of calling `base.log_return` directly. Closes a real gap — `realized_volatility` previously had no non-positive-price guard at all (momentum did), so a bad price would have silently produced NaN/-inf into a vol estimate instead of raising.
- `backtest/engine.compute_portfolio_weights` asserts positions are NaN-free before weighting — `skipna=True` sums could otherwise pass the gross-exposure=1.0 check while a NaN cell still survived into the returned weights.
- `strategy/rules.vol_filtered_positions` raises `SchemaMismatch` on unaligned `positions`/`vol_flag` instead of relying on pandas' implicit `fill_value=0` — matches the alignment guard `backtest/engine.py` already had.
- `feature/volatility.TRADING_DAYS_PER_YEAR = 252` replaces the bare literal.
- `backtest/costs.compute_turnovers` seeds an explicit flat prior row so flat→first-trade prices as real turnover, not free (RECS #10).
- `access/data_api.load` raises `DataSourceError`, not bare `Exception`, on a parquet-read failure.
- `ingestion/fetch_commodities._clean_symbols`: fixed a discarded `.strip()` (was a no-op; also let whitespace-only symbols slip past the empty check).
- `run_ingestion.main()`/`run_clean.main()` now raise `DataSourceError` if any per-symbol write failed, instead of silently exiting 0 with an unread `results` dict (RECS #11).
- Deliberately not touched (explicitly future-phase, not a violation): `backtest/pipeline.py`'s non-running draft, `FEATURES_1D`/`FEATURE_RULES` string-keyed dispatch, universe-wide (not per-sector) cross-sectional rank — all Phase 1/2 per the roadmap below.

## V1 target architecture

```
qr_signal_lab/
  common/        config, paths, errors, logging, types      [unchanged]
  ingestion/                                                  [unchanged]
  cleaning/                                                   [Phase 0 done]
  access/        load() single-symbol -> ADD load_panel(symbols, start, end) -> MultiIndex (field, ticker) columns
  feature/       registry-driven -> params live on the spec, not FEATURES_1D's global `window`
  strategy/      NaN-safe rules [done] -> dispatch off spec, not FEATURE_RULES string matching
  backtest/      costs.py works; engine.py has the math; pipeline.py (run_backtests) is a non-running draft -> rewrite
  evaluate/      NEW — metrics.py, split.py, sweep.py
  spec.py        NEW — StrategySpec dataclass, the unit of research
  run_experiment.py  NEW — single CLI entry point
```

- **`StrategySpec`** (frozen dataclass): `feature_fn`, `feature_params`, `rule_fn`, `rule_params`, `sizing`, `cost_bps`, `universe`, `date_range`; derives `.name`. `universe` defaults to `all_tickers()`, accepts a subset or `SECTORS["energy"]`. Replaces string-keyed registries in `feature/config.py`/`strategy/config.py`. A sweep = list of specs.
- **`BacktestResult`** (dataclass): positions, weights, gross/net returns, turnover, equity, originating spec. Metrics computed *from* this, never inside the backtest.

## Remaining phases

**Phase 1 — Panel + Spec**
- `access/data_api.py`: add `load_panel(symbols, start, end)`.
- New `spec.py`: `StrategySpec`.
- `feature/pipeline.py`: spec-driven, explicit params (retire `FEATURES_1D`'s global window); spec names its input field.
- `strategy/pipeline.py`: dispatch off spec; delete `FEATURE_RULES` string matching.
- `feature/normalization.py`: cross-sectional rank/zscore default to *within-sector* (`sector_of`), not full universe — explicit spec option, never silent.

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
