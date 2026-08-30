# QR-Signal-Lab

Personal quant-research sandbox for commodity futures: daily OHLCV via `yfinance`, 2001→present, 19 tickers across 4 sectors (energy, metals, agriculture, livestock — see `qr_signal_lab/common/universe.py`).

Pipeline: **ingest → clean → access → feature → strategy → backtest → evaluate**. The last three stages are mid-rewrite (see [Status](#status) below) — this is a research environment under active construction, not a finished tool.

## Data discipline (read before trusting any number out of this repo)

Futures continuous tickers are messy in ways that silently wreck backtests:

- **Non-positive prints are real but not tradable.** `CL=F` printed −$37.63 on 2020-04-20 (the real negative WTI settlement). Left unfiltered, one such print can dominate a 25-year backtest. The cleaning layer (`cleaning/clean_commodities.py`) drops any row with non-positive OHLC/adj_close and logs it loudly — do not bypass this.
- **Roll/expiry splices are not P&L.** Yahoo's `=F` continuous tickers stitch contracts at expiry with no back-adjustment, producing single-day moves >40% that no trader ever earned. Not yet auto-detected — treat large single-day moves near contract expiry with suspicion.
- **Tickers have ragged history** (e.g. `BZ=F` starts in 2007). Tolerate leading NaN per ticker; never assume a common start date across the universe.
- **Before trusting any backtest result, check the top single-day P&L contributors.** A great Sharpe ratio driven by 2-3 days out of thousands is a data artifact, not a signal. This check is a first-class part of the evaluation layer being built (Phase 3), not an afterthought.

Past incidents and the fixes that came out of them are logged in `RECS.md` — read it once rather than re-discovering the same bugs.

## Installation

```
pip install -r requirements.txt
```

## Usage

Only ingestion and cleaning have runnable entry points today; everything past that is driven manually (see `notebooks/exploration.ipynb`) until Phase 4 lands `run_experiment.py`.

```
python3 -m qr_signal_lab.ingestion.run_ingestion -v   # -> data/raw/{ticker}.parquet
python3 -m qr_signal_lab.cleaning.run_clean -v        # -> data/clean/{ticker}.parquet
```

## Architecture

```
qr_signal_lab/
  common/        config, paths, typed errors, logging, universe (SECTORS / all_tickers / sector_of)
  ingestion/     yfinance fetch -> data/raw/
  cleaning/      price-validity guard, dedupe -> data/clean/
  access/        load() single-symbol; load_panel() (multi-symbol wide panel) in progress
  feature/       returns.py (sole source of returns), momentum, volatility, normalization
  strategy/      NaN-safe rules (NaN -> flat, never a direction)
  backtest/      costs.py works; engine.py has the math; pipeline.py is being rewritten as run_backtest(spec, panel)
  evaluate/      not started — metrics, IS/OOS split, spec sweeps
  spec.py        not started — StrategySpec, the unit of research
  run_experiment.py  not started — single CLI entry point
```

Conventions held throughout the pure layers (`feature`/`strategy`/`backtest`/`evaluate`): wide DataFrames, dates as index, tickers as columns; no I/O; no mutation; NaN means flat; every rule states its sign convention (`+1 = long`) and is checked against a monotonic-input case; every result carries the spec that produced it.

## Status

**Phase 0 (data discipline) is done** — price-validity guard, dedupe fix, typed errors, NaN-safe rules, correct rank direction. Details in `RECS.md`.

Everything else — panel loading, `StrategySpec`, a working backtest engine, the evaluation layer, and `run_experiment.py` — is scoped but not built. Full phase-by-phase plan lives in `CLAUDE.md`; that file is the source of truth for what's next, this README just orients a new reader.

## Roadmap

See `CLAUDE.md` for the detailed phase plan (Panel + Spec → Backtest → Evaluation → Entry point/tests/docs). Short version: replace string-keyed feature/strategy wiring with a `StrategySpec` dataclass, finish the backtest engine (inverse-vol sizing, correct turnover seeding), add an evaluation layer with mandatory top-P&L-contributor attribution, then wire it all behind `run_experiment.py` with tests.
