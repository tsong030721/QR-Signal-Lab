"""
Ticker universe definition, grouped by sector.

Single source of truth for "what can we trade" - used by ingestion (what to
fetch) and by feature/strategy (cross-sectional grouping). Momentum in corn
and momentum in crude oil aren't directly comparable without first controlling
for sector, so cross-sectional rules should group by sector rather than rank
across the full universe (see StrategySpec.universe in the V1 architecture).

Extend by adding symbols to a sector list below - nothing downstream hardcodes
this universe's size or membership.
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
