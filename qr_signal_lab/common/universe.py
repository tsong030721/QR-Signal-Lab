"""
Ticker universe, grouped by sector - the single source of truth for what's tradable.
Extend by editing SECTORS; nothing downstream hardcodes size or membership.
"""
SECTORS: dict[str, list[str]] = {
    "energy": ["CL=F", "NG=F", "RB=F", "HO=F", "BZ=F"],
    "metals": ["GC=F", "SI=F", "HG=F", "PL=F", "PA=F"],
    "agriculture": ["ZC=F", "ZS=F", "ZW=F", "KC=F", "CT=F", "SB=F", "CC=F"],
    "livestock": ["LE=F", "HE=F"],
}

def all_tickers() -> list[str]:
    """Flat list of every ticker across all sectors, for ingestion."""
    return [ticker for tickers in SECTORS.values() for ticker in tickers]

def sector_of(ticker: str) -> str:
    """Sector containing a given ticker; raises KeyError if not found."""
    for sector, tickers in SECTORS.items():
        if ticker in tickers:
            return sector
    raise KeyError(f"Ticker {ticker} is not assigned to a sector in SECTORS.")
