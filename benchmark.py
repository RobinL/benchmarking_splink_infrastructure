import time
from datetime import datetime

import boto3
from IPython.display import display

from analysis_functions.charts import stacked_mem_cpu
from analysis_functions.duckdb_helpers import load_dict_to_duckdb_using_read_json_auto
from analysis_functions.messages import print_benchmark_info
from analysis_functions.s3 import get_json_file_from_s3
from benchmarking_functions.cloudwatch import (
    get_metric_data_from_ec2_run,
)
from benchmarking_functions.constants import (
    AWS_REGION,
)
from benchmarking_functions.ec2 import poll_instance_id, run_instance_with_user_data
from benchmarking_functions.iam import cleanup_iam_resources, create_all_iam_resources
from benchmarking_functions.s3 import (
    create_bucket_if_not_exists,
    find_benchmarking_file_in_s3,
)

s3_client = boto3.client("s3", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)

start_time = time.time()

create_bucket_if_not_exists(s3_client)

cleanup_iam_resources(iam_client)

create_all_iam_resources(iam_client)

# Allow time for propogation delays
time.sleep(10)


metrics_collection_start_time = datetime.utcnow()


instance = run_instance_with_user_data(ec2_client, "user_data_clone_run_benchmarks.sh")

poll_instance_id(ec2_client, instance)

metrics_collection_end_time = datetime.utcnow()


response = get_metric_data_from_ec2_run(
    cw_client=cw_client,
    instance=instance,
    metrics_collection_start_time=metrics_collection_start_time,
    metrics_collection_end_time=metrics_collection_end_time,
)


cleanup_iam_resources(iam_client)

end_time = time.time()
print(f"Total time taken: {end_time - start_time:.2f} seconds")

# Print results
instance_id = instance["Instances"][0]["InstanceId"]


benchmarking_file = find_benchmarking_file_in_s3(
    s3_client=s3_client,
    instance_id=instance_id,
)


json_data = get_json_file_from_s3(s3_client, benchmarking_file)
conn = load_dict_to_duckdb_using_read_json_auto(json_data, table_name="jd")
display(stacked_mem_cpu(conn, "jd", instance_id))
print_benchmark_info(json_data)
