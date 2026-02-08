2025-12-10
Created repository, got Codespaces up and running
Consolidating vision for V0

2025-12-18
Building error logic foundation
Learning yfinance repo and defining simple ingestion functions

2026-02-08
Picking up from hiatus
Finalized run_ingestion
TODO: Learn the df and pandas basics

Verify end-to-end
    run it and confirm you get 3 parquet files in data/raw/
    confirm basic invariants in the notebook: sorted datetime index, expected columns, sane row counts
Write down the raw data contract
    In a short README note or comments:
    what columns you expect from Yahoo
    what file naming convention you use
    that files are overwritten each run in V0
Commit V0 ingestion
    This is a milestone commit.
Start cleaning (next module)
    Create qr_signal_lab/cleaning/clean_commodities.py that:
        loads raw parquet
        standardizes column names (lowercase, consistent)
        enforces dtypes
        de-dupes + sorts
        handles missing dates explicitly (decide policy)
        writes data/clean/{symbol}.parquet
Add an access layer stub
    qr_signal_lab/access/data_api.py with:
    load(symbol, start=None, end=None, source="clean") -> DataFrame