from datetime import datetime

# Parameter set
PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}
INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}

# Research parameters
TICKERS = ["CL=F", "GC=F", "NG=F", "ZC=F", "HG=F"]
START_DATE = "2000-01-01"
END_DATE = None
INTERVAL = "1d"
RAW_DIR = "data/raw"