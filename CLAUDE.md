# CLAUDE.md

## What this is

Personal quant-research sandbox for testing trading hypotheses on commodity futures (daily, yfinance, 2001→present). Pipeline: ingest → clean → feature → strategy → backtest → evaluate (evaluate doesn't exist yet — building it is the point of this refactor).

Universe is 19 tickers across 4 sectors, defined in `common/universe.py` (`SECTORS` dict + `all_tickers()`/`sector_of()`) — energy, metals, agriculture, livestock. It started as 5 test tickers; that was never a hard limit, so nothing downstream should assume a fixed size or membership. Edit `common/universe.py` to add/remove symbols; `ingestion/config.TICKERS` just calls `all_tickers()`. Tickers have ragged history (e.g. `BZ=F` starts 2007, `PL=F`/`LE=F` are shorter) — panel loading and cross-sectional features must tolerate leading NaN per ticker, not assume a common start date.

`docs/v0.md`/`v1.md` describe the original phased plan — **superseded by the V1 target below.** `RECS.md` has the compact list of mistakes made so far (data discipline + architecture) — read it once, don't re-derive it.

## Commands

```
pip install -r requirements.txt
python3 -m qr_signal_lab.ingestion.run_ingestion -v   # -> data/raw/{sym}.parquet
python3 -m qr_signal_lab.cleaning.run_clean -v        # -> data/clean/{sym}.parquet
```
No tests/linter/build yet (Phase 4 adds pytest). No entry point for feature/strategy/backtest yet (Phase 4 adds `run_experiment.py`) — until then, drive manually via a script, following the pattern in `notebooks/exploration.ipynb`.

## Status: Phase 0 is DONE. Do not redo it.

Landed: price-validity guard in `cleaning/clean_commodities.py` (`_handle_missing` drops any row with a non-positive `open/high/low/close/adj_close`, logged loudly); dedupe bug fixed (`~duplicated`); typed errors (`DataValidationError`/`DataSourceError`) replace bare `Exception`; new `feature/returns.py` is the **single canonical source of returns** (`simple_returns`/`log_returns`, raises `DataValidationError` on any non-positive price as defense-in-depth); `pct_return`/`log_return` removed from `feature/config.FEATURES_1D` (returns are not a feature); `strategy/rules.py` rules are NaN-safe (NaN → flat, never a direction) and rank direction is fixed (`csec_rank_positions`: `top_pct=0.8`→long, `bottom_pct=0.2`→short, assumes ascending rank where 1.0=highest); `feature/volatility.vol_regime_flag` returns NaN (not 0) when unknown, and `vol_filtered_positions` treats NaN as high-vol/do-not-trade via `.fillna(1)`.

Verified: momentum strategy final equity went from **139,444 (+39%, artifact-driven) → 84,057 (−16%, real)** after the fix. This is the correct, expected result — do not "debug" a strategy that now loses money without first checking whether Phase 0's guards are what changed it.

## V1 target architecture

```
qr_signal_lab/
  common/        config, paths, errors, logging, types      [unchanged]
  ingestion/                                                  [unchanged]
  cleaning/                                                   [Phase 0 done]
  access/        load() single-symbol -> ADD load_panel(symbols, start, end) -> MultiIndex (field, ticker) columns
  feature/       registry-driven -> params live on the spec, not in FEATURES_1D's global `window`
  strategy/      NaN-safe rules [done] -> dispatch off spec, not FEATURE_RULES string matching
  backtest/      costs.py works; engine.py has the math; pipeline.py (run_backtests) is a non-running draft -> rewrite
  evaluate/      NEW — metrics.py, split.py, sweep.py
  spec.py        NEW — StrategySpec dataclass, the unit of research
  run_experiment.py  NEW — single CLI entry point
```

Two ideas carry the rest of the design:
- **`StrategySpec`** (frozen dataclass: `feature_fn`, `feature_params`, `rule_fn`, `rule_params`, `sizing`, `cost_bps`, `universe`, `date_range`, derives its own `.name`). `universe` should default to `common.universe.all_tickers()` but accept a subset or a single sector (`common.universe.SECTORS["energy"]`) so a hypothesis can be tested sector-by-sector, not just on the full 19. Replaces the string-keyed registries in `feature/config.py`/`strategy/config.py`. A parameter sweep is just a list of specs.
- **`BacktestResult`** (dataclass: positions, weights, gross/net returns, turnover, equity, the originating spec). Metrics are computed *from* this, never inside the backtest itself.

## Remaining phases

**Phase 1 — Panel + Spec**
- `access/data_api.py`: add `load_panel(symbols, start, end)`.
- New `spec.py`: `StrategySpec`.
- `feature/pipeline.py`: take a spec, params explicit (retire `FEATURES_1D`'s global window); let the spec name its input field (nothing currently uses non-`close` fields).
- `strategy/pipeline.py`: dispatch off spec; delete `FEATURE_RULES` string matching.
- `feature/normalization.py` cross-sectional rank/zscore: default to ranking *within sector* (`common.universe.sector_of`), not across the full 19-ticker universe — comparing corn's momentum percentile to crude's isn't meaningful without controlling for sector first. Make this an explicit spec option, don't silently pick one.

**Phase 2 — Finish backtest**
- `backtest/pipeline.py`: rewrite as `run_backtest(spec, panel) -> BacktestResult`. Sequence: shift → align → size → weights → turnover → costs → net → equity.
- `backtest/costs.py`: `compute_turnovers` uses `.diff()` so the first-ever trade (flat→position) is free turnover — seed from an explicit zero row.
- New `backtest/sizing.py`: inverse-vol weights + portfolio vol target, using `realized_volatility` (currently computed and unused for sizing — see RECS.md #7).
- Fill or delete `backtest/config.py` (currently empty).
- Assert the lag contract once, centrally: position at *t* uses info ≤ *t*, earns return *t*→*t+1*.

**Phase 3 — Evaluation**
- `evaluate/metrics.py`: Sharpe, ann. return/vol, max drawdown, Calmar, hit rate, avg turnover, t-stat on mean daily return.
- `evaluate/split.py`: fixed IS/OOS boundary, declared once.
- `evaluate/sweep.py`: run a list of specs → metrics DataFrame keyed by spec name. Report the *distribution* of Sharpe across params, not the max.
- **Top-contributor report on every result** (N biggest single-day P&L days) — this is what would have caught the Phase-0 bug on day one. Non-negotiable, add it before trusting any new spec's numbers.

**Phase 4 — Entry point, tests, docs**
- `run_experiment.py`: `python3 -m qr_signal_lab.run_experiment --spec <name>` → `results/{spec_name}/{metrics.json, equity.parquet, spec.json}`.
- `tests/`: fixtures with known answers (monotonic price → +1 momentum; NaN column → 0 position; hand-computed Sharpe on a known return series). Pin `requirements.txt` versions; add `pytest`.
- Rewrite `README.md`: what this is, the data-discipline caveat up front, install, the commands, one worked example, repo layout. Move its current markdown-cheatsheet intro to `docs/useful.md`.
- Mark `docs/v0.md`/`v1.md` historical; keep `docs/lab_log.md` current.
- Thin `notebooks/exploration.ipynb` down to a consumer of `run_experiment` — no pipeline logic in notebooks.

## Conventions to hold throughout

- I/O only in `ingestion`/`cleaning`/`access`. `feature`/`strategy`/`backtest`/`evaluate` are pure: DataFrame/Series in, same out, index preserved, no mutation.
- Wide DataFrames, dates as index, tickers as columns, from the feature layer on.
- Returns come from `feature/returns.py` only — never re-derived elsewhere.
- NaN means flat. Every rule states its NaN behavior; assert zero NaN survives into positions.
- Every rule states its sign convention (`+1 = long`) and should be checked against a monotonic-input case before trusting it.
- A strategy is a `StrategySpec` value, not a set of matching string keys.
- Raise typed errors from `common/errors.py` at the point of failure; catch only at layer boundaries.
- Every result carries the spec that produced it — no number without provenance.
- Before trusting a good Sharpe: check the top P&L contributors. A great-looking result is a bug report until attribution is checked.
