import boto3

from analysis_functions.duckdb_helpers import load_dicts_to_duckdb_using_read_json_auto
from analysis_functions.s3 import get_json_files_from_s3_prefix
from benchmarking_functions.constants import (
    AWS_REGION,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
)

s3_client = boto3.client("s3", region_name=AWS_REGION)
dict_of_jsons = get_json_files_from_s3_prefix(
    s3_client, OUTPUT_S3_BUCKET, OUTPUT_S3_FOLDER
)
conn = load_dicts_to_duckdb_using_read_json_auto(dict_of_jsons, "df")


query = """
    SELECT
        datetime,
        custom.run_label,
        custom.max_pairs,
        custom.instance_id,
        benchmarks[1].name as benchmark_name,
        benchmarks[1].stats.min as min_time,
        benchmarks[1].stats.mean as mean_time,
        machine_info.cpu.count,
        machine_info.cpu.brand_raw,
    FROM df
    ORDER BY datetime DESC"""
conn.execute(query).df()
