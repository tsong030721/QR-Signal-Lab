# Recommendations — read this, not the git log

Compact list of the mistakes worth remembering. Data-discipline items include what to do next time and the financial intuition that should have flagged it. Fixed items are marked `[FIXED]`.

## Data discipline

1. **`[FIXED]` Negative/invalid prices reached `pct_change`/`log`.** `CL=F` printed −$37.63 on 2020-04-20 (real event — negative WTI settlement). Unfiltered, this became a −306% "return" and made a 25-year backtest look like +39% instead of −16% (three days carried the entire result).
   - **COA:** validate prices at the cleaning boundary — assert `price > 0` before anything downstream touches them. Never let a feature/return function receive raw exchange data unchecked.
   - **Intuition:** a return below −100% is not possible for a long position. Any number outside a sane range (say, ±20% daily for a single commodity) should make you stop and look at the raw print, not the strategy.

2. **Roll/expiry splices are being treated as tradable P&L.** Yahoo's `=F` continuous tickers stitch contracts at expiry with no back-adjustment; `NG=F` shows 47.5%/46.5% one-day moves on expiry dates.
   - **COA:** either source back-adjusted continuous contracts, or detect and exclude roll-date jumps explicitly (flag the day of/after expiry).
   - **Intuition:** no futures trader earns the calendar-spread jump between two different contracts. If a "return" only exists because you compared prices of two different instruments, it isn't a return.

3. **No sanity check ever compared "results" to "plausible."** The strategy ran, produced a curve, and was trusted.
   - **COA:** for every backtest, always ask "what are the 10 biggest single-day P&L contributions, and are they real?" before looking at Sharpe.
   - **Intuition:** if 2 days out of 6,400 explain your entire edge, you haven't found a signal — you've found a data artifact.

4. **The price guard (#1) generalized beyond the one known incident on the first re-run of a bigger universe.** Expanding to 19 tickers immediately caught `CT=F` with `open=0.0` on the still-forming current-day bar — a live yfinance data artifact, not a market event — and dropped it automatically.
   - **Intuition:** this is what a validated guard is supposed to feel like: boring. You shouldn't have to remember to re-check for bad ticks every time the universe grows — the check should live at the boundary once and catch it for you.

## Strategy / rules correctness

5. **`[FIXED]` NaN silently became a short.** `1 if x > 0 else -1` on an un-warmed-up (NaN) feature: `NaN > 0` is `False`, so short. 214 warm-up cells were trading a fake signal.
   - **Intuition:** "no information" and "bearish information" are not the same thing. A rule that can't spell "flat" will invent a direction for you.

6. **`[FIXED]` Cross-sectional rank was inverted — a momentum rule was longing the worst performer.** `rank(ascending=True)` gives the *lowest* value the *lowest* percentile; the original code longed low percentiles. Verified: CL=F (best momentum) → short, HG=F (worst) → long.
   - **Intuition:** always sanity-check a cross-sectional rule on one row by hand: best asset should get the sign you intended. If you have to think hard about which threshold is "top," so will the next bug.

## Architecture (no COA needed — these are code-structure calls, not spottable-in-data lessons)

7. **String-keyed wiring is load-bearing.** `feature/pipeline.py` builds keys like `f"{label}_{normalizer}"`; `strategy/config.py` hardcodes `"momentum_return_rank"` to match. Untypeable, unsweepable, breaks silently if `normalize=False`.
8. **Equal-notional sizing, not equal-risk.** `CL=F`/`NG=F` vol (78%/61% ann.) dwarfs `GC=F` (18%); an "equal weight" book is really a crude/natgas bet. `realized_volatility` is already computed and unused for sizing. Bigger universe makes this worse, not better — 19 tickers of wildly different vol still get equal notional.
9. **No evaluation layer.** No metrics, no IS/OOS split, no sweep. `FEATURES_1D` bakes one global `window` per feature, which structurally prevents sweeping window as a parameter.
10. **Backtest engine was a non-running draft** (`backtest/pipeline.py` referenced six undefined names, ignored its own `cost_bps` argument). `costs.compute_turnovers` uses `.diff()`, so the first-ever trade (going from flat to a position) is priced as free turnover.
11. **Errors and results are computed and discarded.** `run_ingestion`/`run_clean` build a `results` dict per symbol and never inspect it — a failed symbol doesn't fail the run.
12. **The universe was hardcoded to 5 tickers with no sector concept.** Fixed by adding `common/universe.py` (sector-grouped, `all_tickers()`/`sector_of()`); everything downstream already took symbols as a parameter, so this was a one-file change. Cross-sectional rank/zscore should rank *within sector*, not across the whole universe — see CLAUDE.md Phase 1.
