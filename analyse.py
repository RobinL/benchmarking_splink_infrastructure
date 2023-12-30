import os
import shutil

import altair as alt
import boto3
import duckdb
import pandas as pd
from botocore.exceptions import NoCredentialsError


def create_and_clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)


def download_s3_bucket_contents(*, bucket_name, local_directory, s3_folder_path):
    s3 = boto3.client("s3")
    prefix = s3_folder_path.rstrip("/") + "/"  # Ensure the folder path ends with '/'

    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                s3_file_name = obj["Key"]
                if not s3_file_name.endswith("/"):  # Skip directories
                    local_file_name = os.path.join(
                        local_directory, os.path.basename(s3_file_name)
                    )
                    s3.download_file(bucket_name, s3_file_name, local_file_name)
        else:
            print("No files found in the specified folder")
    except NoCredentialsError:
        print("Credentials not available")
    except KeyError:
        print("Bucket is empty or does not exist")


bucket_name = "robinsplinkbenchmarks"
s3_directory = "pytest_benchmark_results"
local_directory = "benchmarking_json"


create_and_clear_directory(local_directory)

download_s3_bucket_contents(
    bucket_name=bucket_name,
    local_directory=local_directory,
    s3_folder_path=s3_directory,
)

conn = duckdb.connect()

json_folder = "benchmarking_json"

query = f"""
    SELECT
        datetime,
        custom.run_label,
        custom.max_pairs,
        benchmarks[1].name as benchmark_name,
        benchmarks[1].stats.min as min_time,
        benchmarks[1].stats.mean as mean_time,
        machine_info.cpu.count,
        machine_info.cpu.brand_raw,
    FROM read_json_auto('{json_folder}/*.json')
    ORDER BY datetime DESC"""
conn.execute(query).df()


json_folder = "benchmarking_json"

query = f"""
    with i1 as (
        SELECT
            datetime,
            custom.run_label as run_label,
            custom.max_pairs as max_pairs,
            benchmarks[1].name as benchmark_name,
            benchmarks[1].stats.min as min_time,
            benchmarks[1].stats.mean as mean_time,
            machine_info.cpu.count as cpu_count,
            machine_info.cpu.brand_raw as cpu_brand_raw,

            unnest(list_zip(
                custom.metrics.MetricDataResults[1].Timestamps,
                custom.metrics.MetricDataResults[1].Values,
                custom.metrics.MetricDataResults[2].Timestamps,
                custom.metrics.MetricDataResults[2].Values
            )) as zipped,


        FROM read_json_auto('{json_folder}/*.json')
        where datetime = '2023-12-30T19:43:33.685711'
        ORDER BY datetime DESC
    )
    select
        datetime,
        run_label,
        max_pairs,
        benchmark_name,
        min_time,
        mean_time,
        cpu_count,
        cpu_brand_raw,
        CAST(zipped['list_1'] AS TIMESTAMP) as mem_timestamp,
        zipped['list_2'] as mem_value,
        CAST(zipped['list_3'] AS TIMESTAMP) as cpu_timestamp,
        zipped['list_4'] as cpu_value

    from i1
    """
df = conn.execute(query).df()


mem_chart = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=alt.X("mem_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),  # Custom format
        y="mem_value:Q",
        color=alt.value("blue"),
        tooltip=["datetime", "mem_value"],
    )
    .properties(title="Memory Usage Over Time", width=600, height=300)
)


cpu_chart = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=alt.X("cpu_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),  # Custom format
        y="cpu_value:Q",
        color=alt.value("red"),
        tooltip=["datetime", "cpu_value"],
    )
    .properties(title="CPU Usage Over Time", width=600, height=300)
)


stacked_chart = alt.vconcat(mem_chart, cpu_chart).resolve_scale(
    x="shared", y="independent"
)


stacked_chart
