"""
Script to loop through the desired tickers.
Writes each DataFrame to data/raw/{ticker}.parquet
Logs rows, min/max date, failures for each ticker.
"""
from pathlib import Path
import argparse
import logging

from . import config
from .fetch_commodities import fetch_batch_separate

logger = logging.getLogger(__name__)

def run_ingestion(cfg) -> dict[str, str]:
    results = dict()

    # Fetch DataFrames
    symbols = cfg.TICKERS
    df_list = fetch_batch_separate(
        symbols,
        start=cfg.START_DATE,
        end=cfg.END_DATE,
        interval=cfg.INTERVAL
    )

    # Write parquet files to data/raw
    root = Path(__file__).resolve().parents[2]
    out_dir = root / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    for symbol, df in zip(symbols, df_list):
        try:
            df.to_parquet(
                out_dir / f"{symbol}.parquet",
                engine="pyarrow",
                compression="snappy"
            )

            logger.info(
                "Wrote %s | rows = %d | start=%s | end =%s",
                symbol,
                len(df),
                df.index.min(),
                df.index.max(),
            )

            results[symbol] = "ok"
        except Exception as e:
            logger.exception("Failed to write %s", symbol)
            results[symbol] = str(e)
    
    return results

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Enable INFO logging (-v) or DEBUG logging (-vv)",
        default = 0,
    )
    args = parser.parse_args()

    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    if args.verbose == 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    results =run_ingestion(config)

if __name__ == "__main__":
    main()