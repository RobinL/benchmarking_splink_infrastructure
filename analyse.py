import os
import shutil

import boto3
import duckdb
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
