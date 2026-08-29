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

## Status: Phase 0 DONE — do not redo

- Price-validity guard: `cleaning/clean_commodities.py._handle_missing` drops any row with non-positive OHLC/adj_close, logs loudly.
- Dedupe bug fixed (`~duplicated`); bare `Exception` → typed errors (`DataValidationError`/`DataSourceError`).
- `feature/returns.py` is the sole source of returns (`simple_returns`/`log_returns`), raises `DataValidationError` on non-positive price as defense-in-depth. `pct_return`/`log_return` removed from `FEATURES_1D` — returns aren't a feature.
- `strategy/rules.py`: NaN-safe (NaN → flat, never a direction); rank direction fixed (`csec_rank_positions`: `top_pct=0.8`→long, `bottom_pct=0.2`→short, ascending rank, 1.0=highest).
- `feature/volatility.vol_regime_flag` returns NaN (not 0) when unknown; `vol_filtered_positions` treats NaN as high-vol via `.fillna(1)`.
- Verification + incident detail: RECS.md #1, #5, #6.

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

- I/O only in `ingestion`/`cleaning`/`access`. `feature`/`strategy`/`backtest`/`evaluate` are pure: same in/out shape, index preserved, no mutation.
- Wide DataFrames, dates as index, tickers as columns, from the feature layer on.
- Returns come from `feature/returns.py` only — never re-derived elsewhere.
- NaN means flat. Every rule states its NaN behavior; assert zero NaN survives into positions.
- Every rule states its sign convention (`+1 = long`); check against a monotonic-input case before trusting it.
- A strategy is a `StrategySpec` value, not a set of matching string keys.
- Raise typed errors from `common/errors.py` at the point of failure; catch only at layer boundaries.
- Every result carries the spec that produced it — no number without provenance.
- Before trusting a good Sharpe: check the top P&L contributors. A great-looking result is a bug report until attribution is checked.
