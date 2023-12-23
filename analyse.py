import os
import shutil

import boto3
import duckdb
from botocore.exceptions import NoCredentialsError


def create_and_clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)


def download_s3_bucket_contents(bucket_name, local_directory):
    s3 = boto3.client("s3")
    try:
        for obj in s3.list_objects_v2(Bucket=bucket_name)["Contents"]:
            s3_file_name = obj["Key"]
            local_file_name = os.path.join(local_directory, s3_file_name)
            s3.download_file(bucket_name, s3_file_name, local_file_name)
    except NoCredentialsError:
        print("Credentials not available")
    except KeyError:
        print("Bucket is empty or does not exist")


bucket_name = "robinsplinkbenchmarks"
local_directory = "benchmarking_json"

create_and_clear_directory(local_directory)
download_s3_bucket_contents(bucket_name, local_directory)


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
