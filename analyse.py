import boto3

from analysis_functions.duckdb_helpers import load_dicts_to_duckdb_using_read_json_auto
from analysis_functions.s3 import get_json_files_from_s3_prefix
from benchmarking_functions.constants import (
    AWS_REGION,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
)

s3_client = boto3.client("s3", region_name=AWS_REGION)

instances = [
    "i-0a544c96bb373cfa0",
    "i-0ae0b81108ec3c84d",
    "i-03cc8a3e708bea937",
    "i-056ebcd9cb91bc6ce",
    "i-08cc3110acd7b818b",
]

final_dict = {}
for i in instances:
    dict_of_jsons = get_json_files_from_s3_prefix(
        s3_client, OUTPUT_S3_FOLDER + f"/benchmarking_results_{i}"
    )
    final_dict = {**final_dict, **dict_of_jsons}
conn = load_dicts_to_duckdb_using_read_json_auto(final_dict, "df")

conn.execute("select * from df").df().iloc[0]["custom"]


query = """
with unnested as (
    SELECT
        unnest(benchmarks).name as benchmark_name,
        custom.run_label,

        custom.instance_id,


        custom.max_pairs,
        custom.num_input_rows,
        custom.instance_type,
        unnest(benchmarks).stats.mean as mean_seconds,
        machine_info.cpu.count,

        machine_info.cpu.brand_raw,


    FROM df
    ), grouped as(
    select * ,
    CASE
        WHEN benchmark_name LIKE '%estimate_probability_two_rand%' THEN 0
         WHEN benchmark_name LIKE '%estimate_u%' THEN 1
         WHEN benchmark_name LIKE '%estimate_parameters_using%' THEN 2
         WHEN benchmark_name LIKE '%predict%' THEN 3
         ELSE 4
    END as benchmark_group1,

    CASE
        WHEN benchmark_name LIKE '%estimate_probability_two_rand%' THEN 'estimate_probability_two_random_records_match'
         WHEN benchmark_name LIKE '%estimate_u%' THEN 'estimate_u'
         WHEN benchmark_name LIKE '%estimate_parameters_using%' THEN 'estimate_parameters_using_expectation_maximisation'
         WHEN benchmark_name LIKE '%predict%' THEN 'predict'
         ELSE 4
    END as benchmark_function,


    CASE
    WHEN benchmark_name LIKE '%no_salt%' THEN 0
        WHEN benchmark_name LIKE '%salt_2%' THEN 1
        WHEN benchmark_name LIKE '%cpu_salted%' THEN 2
        ELSE 3
    END as benchmark_group2,

    CASE
    WHEN benchmark_name LIKE '%no_salt%' THEN 'no_salt'
    WHEN benchmark_name LIKE '%salt_2%' THEN 'salt_2'
    WHEN benchmark_name LIKE '%cpu_salted%' THEN 'cpu_salted'
    END as salt_type

    from unnested)

    select mean_seconds,
    benchmark_function,
    salt_type,
    run_label,
    max_pairs,
    num_input_rows,
    count,
    instance_id,
    instance_type,
    brand_raw
    from grouped
    where benchmark_function = 'predict'
    ORDER BY benchmark_group1, count,benchmark_group2, run_label
    """
conn.execute(query).df()
conn.execute(query).df().sort_values("mean_seconds")
