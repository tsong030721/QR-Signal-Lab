"""
Configuration constants for the backtest layer.
"""

# Starting notional for equity-curve compounding - a display/bookkeeping
# constant, not a research parameter: it scales the equity curve's units but
# never affects returns, turnover, or any spec-driven decision.
INITIAL_CAPITAL = 100_000

# Canonical tradable price field backtest returns are derived from - matches
# cleaning/config.PRICE_COLUMNS' adj_close (split/dividend-adjusted).
PRICE_FIELD = "adj_close"
