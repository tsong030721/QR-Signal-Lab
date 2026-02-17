"""
Script to standardize all parquets in data/raw.
Writes each cleaned DataFrame to data/clean/{symbol}.parquet.
"""
import argparse

from .clean_commodities import clean_many
from ..common import logging, paths

logger = logging.get(__name__)

def run_clean() -> dict[str, str]:
    results = dict()

    # Clean DataFrames
    try:
        symbols = paths.get_symbols()
        df_list = clean_many(symbols)
    except Exception as e:
        logger.error(e)
        raise
    
    # Write DataFrames to data/clean
    for symbol, df in zip(symbols, df_list):
        try:
            path = paths.clean_path(symbol)
            df.to_parquet(
                path,
                engine="pyarrow",
                compression="snappy"
            )

            logger.info(
                "Wrote clean %s | rows = %d | start=%s | end =%s",
                symbol,
                len(df),
                df.index.min(),
                df.index.max(),
            )

            results[symbol] = "ok"
        except Exception as e:
            logger.exception(f"Failed to write {symbol}")
            results[symbol] = e
    
    return results

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        help="Enable INFO logging (-v) or DEBUG logging (-vv)",
        default=0,
    )
    args = parser.parse_args()

    logging.configure(args.verbose)

    results = run_clean()

if __name__ == "__main__":
    main()