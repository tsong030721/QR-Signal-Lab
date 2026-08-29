from datetime import datetime

from ..common.universe import all_tickers

# Parameter set
PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}

# Research parameters. Universe is defined by sector in common/universe.py -
# edit there to add/remove tickers, not here.
TICKERS = all_tickers()
START_DATE = "2001-01-01"
END_DATE = None
INTERVAL = "1d"
