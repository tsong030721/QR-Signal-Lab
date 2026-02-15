"""
Script to loop through the desired tickers.
Writes each DataFrame to data/raw/{ticker}.parquet
Logs rows, min/max date, failures for each ticker.
"""
from pathlib import Path
import argparse

from . import config
from .fetch_commodities import fetch_batch_separate
from ..common import logging, paths
from ..common.errors import InvalidRequest, DataSourceError, EmptyData

logger = logging.get(__name__)

def run_ingestion(cfg) -> dict[str, str]:
    results = dict()

    # Fetch DataFrames
    symbols = cfg.TICKERS
    try:
        df_list = fetch_batch_separate(
            symbols,
            start=cfg.START_DATE,
            end=cfg.END_DATE,
            interval=cfg.INTERVAL
        )
    except EmptyData as e:
        logger.warning(e)
        return results
    except (DataSourceError, InvalidRequest) as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.exception(f"Unexpected failure during ingestion: {e}")
        raise

    for symbol, df in zip(symbols, df_list):
        try:
            df.to_parquet(
                paths.raw_path(symbol),
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

    logging.configure(args.verbose)

    results = run_ingestion(config)

if __name__ == "__main__":
    main()