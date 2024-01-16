import pandas as pd
from splink.duckdb.linker import DuckDBLinker

df = pd.read_parquet(
    "/Users/robinlinacre/Documents/data_linking/run_splink_benchmarks_in_ec2/3m_prepared.parquet"
)
linker = DuckDBLinker(df, "./splink_model_i-0bde982fc2f1ec689_f128871.json")
linker.match_weights_chart()
