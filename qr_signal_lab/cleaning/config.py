# ----------------------------
# Schema
# ----------------------------
DTYPES = {
    'adj_close': 'float64',
    'close': 'float64',
    'high': 'float64',
    'low': 'float64',
    'open': 'float64',
    'volume': 'int64'
    }

# Columns that must be strictly positive to be usable as a price
PRICE_COLUMNS = ['adj_close', 'close', 'high', 'low', 'open']