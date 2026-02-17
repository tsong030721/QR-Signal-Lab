Logging
logger.debug(...)     # dev detail
logger.info(...)      # normal progress
logger.warning(...)   # recoverable issues
logger.error(...)     # failure, no traceback
logger.exception(...) # failure WITH traceback (inside except)

Dataframe
1. Inspection
df.head()        # first 5 rows (what does the data look like?)
df.tail()        # last 5 rows
df.shape         # (n_rows, n_cols)
df.columns       # column labels
df.dtypes        # data type per column
df.empty         # True if df has zero rows
df.info()        # schema + non-null counts (quick health check)

2. Indexing
df.index         # row labels (often timestamps)
df.index.min()   # earliest timestamp
df.index.max()   # latest timestamp
df.sort_index()  # ensure chronological order
df.loc[start:end]  # slice rows by index labels (dates!)

3. Selecting
df["Close"]              # select one column (Series)
df[["Open", "Close"]]    # select multiple columns
df.loc[rows, cols]       # label-based row/column selection
df.iloc[i:j]             # position-based row selection

4. Reshaping
df.copy()                # defensive copy
df.rename(columns={...}) # rename columns
df.drop(columns=[...])   # remove columns
df.reset_index()         # move index → column
df.set_index("date")     # promote column → index

5. Missing data handling
df.isna()                # True where values are missing
df.notna()               # True where values exist
df.dropna()              # remove rows with missing data
df.fillna(value)         # replace missing values

6. Aggregations
df.mean()        # column-wise average
df.sum()         # column-wise sum
df.min()         # column-wise min
df.max()         # column-wise max
df.describe()    # count/mean/std/min/max/quantiles

7. Applying custom logic
df.apply(func, axis=0)   # apply function to each column
df.apply(func, axis=1)   # apply function to each row (slow)

8. IO
df.to_parquet(path)      # write df to parquet
pd.read_parquet(path)    # read parquet → df
df.to_csv(path)          # write csv
pd.read_csv(path)        # read csv