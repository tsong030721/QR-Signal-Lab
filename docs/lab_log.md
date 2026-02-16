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

2026-02-14
Learn some pandas (Data School)
Verify end-to-end for run_ingestion; examine the raw parquets
Document raw data contract

2026-02-15
Centralize helpers for path, logging, types
Clean up run_ingestion using global helpers

2026-02-16

Start cleaning (next module)
    Create qr_signal_lab/cleaning/clean_commodities.py that:

        writes data/clean/{symbol}.parquet
Add an access layer stub
    qr_signal_lab/access/data_api.py with:
    load(symbol, start=None, end=None, source="clean") -> DataFrame