# Recommendations — read this, not the git log

Mistakes worth remembering, with fixes and the intuition that should have caught them. `[FIXED]` = resolved.

## Data discipline

1. **`[FIXED]` Negative/invalid prices reached `pct_change`/`log`.** `CL=F` printed −$37.63 on 2020-04-20 (real negative WTI settlement). Unfiltered → a −306% "return", inflating a 25-year backtest to +39% instead of −16% (3 days drove the entire result).
   - **Fix:** validate at the cleaning boundary — assert `price > 0` before anything downstream touches it.
   - **Intuition:** a return below −100% is impossible for a long position. Any daily move outside a sane range (~±20%) means look at the raw print, not the strategy.

2. **Roll/expiry splices treated as tradable P&L.** Yahoo's `=F` continuous tickers stitch contracts at expiry with no back-adjustment; `NG=F` shows 47.5%/46.5% one-day moves on expiry dates.
   - **Fix:** source back-adjusted contracts, or detect/exclude roll-date jumps explicitly.
   - **Intuition:** no trader earns the calendar-spread jump between two different contracts — that's not a return.

3. **No check ever compared "results" to "plausible."** The strategy ran, produced a curve, and was trusted.
   - **Fix:** for every backtest, check the top 10 single-day P&L contributions before looking at Sharpe.
   - **Intuition:** if 2 days out of 6,400 explain your entire edge, that's a data artifact, not a signal.

4. **The price guard (#1) generalized on the first bigger-universe run.** Expanding to 19 tickers caught `CT=F` with `open=0.0` on a still-forming bar — a live yfinance artifact, dropped automatically.
   - **Intuition:** a validated guard should feel boring — it catches new bad ticks without you having to remember to re-check.

## Strategy / rules correctness

5. **`[FIXED]` NaN silently became a short.** `1 if x > 0 else -1` on NaN: `NaN > 0` is `False` → short. 214 warm-up cells traded a fake signal.
   - **Intuition:** "no information" ≠ "bearish." A rule that can't spell "flat" invents a direction.

6. **`[FIXED]` Cross-sectional rank was inverted** — longing the worst performer. `rank(ascending=True)` gives the lowest value the lowest percentile; the original code longed low percentiles. Verified: CL=F (best momentum) → short, HG=F (worst) → long.
   - **Intuition:** sanity-check a cross-sectional rule on one row by hand — the best asset should get the sign you intended.

## Architecture (code-structure calls, not data-spottable)

7. **String-keyed wiring is load-bearing.** `feature/pipeline.py` builds keys like `f"{label}_{normalizer}"`; `strategy/config.py` hardcodes `"momentum_return_rank"` to match. Untypeable, unsweepable, breaks silently if `normalize=False`.
8. **Equal-notional sizing, not equal-risk.** `CL=F`/`NG=F` vol (78%/61% ann.) dwarfs `GC=F` (18%) — "equal weight" is really a crude/natgas bet. `realized_volatility` is already computed and unused for sizing.
9. **No evaluation layer.** No metrics, IS/OOS split, or sweep. `FEATURES_1D` bakes one global `window` per feature, blocking window sweeps.
10. **Backtest engine was a non-running draft** (`backtest/pipeline.py` referenced six undefined names, ignored its own `cost_bps` argument). `costs.compute_turnovers` uses `.diff()`, pricing the first-ever trade (flat→position) as free.
11. **Errors/results computed and discarded.** `run_ingestion`/`run_clean` build a `results` dict per symbol and never inspect it — a failed symbol doesn't fail the run.
12. **Universe hardcoded to 5 tickers, no sector concept.** Fixed via `common/universe.py` (sector-grouped, `all_tickers()`/`sector_of()`) — a one-file change since downstream already took symbols as a parameter. Cross-sectional rank/zscore should rank within-sector, not universe-wide (CLAUDE.md Phase 1).
