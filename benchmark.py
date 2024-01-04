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
    CLOUDWATCH_IAM_POLICY_NAME,
    EC2_IAM_INSTANCE_PROFILE_NAME,
    EC2_IAM_ROLE_NAME,
    IMAGEID,
    INSTANCE_TYPE,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
    S3_IAM_POLICY_NAME,
)
from benchmarking_functions.ec2 import poll_instance_id
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

create_bucket_if_not_exists(s3_client, OUTPUT_S3_BUCKET, AWS_REGION)

cleanup_iam_resources(iam_client, EC2_IAM_ROLE_NAME, EC2_IAM_INSTANCE_PROFILE_NAME)


create_all_iam_resources(
    iam_client,
    EC2_IAM_ROLE_NAME,
    S3_IAM_POLICY_NAME,
    CLOUDWATCH_IAM_POLICY_NAME,
    EC2_IAM_INSTANCE_PROFILE_NAME,
    OUTPUT_S3_BUCKET,
)

# Allow time for propogation delays
time.sleep(10)


def read_user_data_script(file_path):
    with open(file_path, "r") as file:
        return file.read()


user_data_file_path = "user_data_clone_run_benchmarks.sh"
user_data_script = read_user_data_script(user_data_file_path)


metrics_collection_start_time = datetime.utcnow()


instance = ec2_client.run_instances(
    ImageId=IMAGEID,
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    UserData=user_data_script,
    IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE_NAME},
    InstanceInitiatedShutdownBehavior="terminate",
)

poll_instance_id(ec2_client, instance)


metrics_collection_end_time = datetime.utcnow()


response = get_metric_data_from_ec2_run(
    cw_client=cw_client,
    instance=instance,
    instance_type=INSTANCE_TYPE,
    metrics_collection_start_time=metrics_collection_start_time,
    metrics_collection_end_time=metrics_collection_end_time,
)


cleanup_iam_resources(iam_client, EC2_IAM_ROLE_NAME, EC2_IAM_INSTANCE_PROFILE_NAME)

end_time = time.time()
print(f"Total time taken: {end_time - start_time:.2f} seconds")

# Print results
instance_id = instance["Instances"][0]["InstanceId"]


benchmarking_file = find_benchmarking_file_in_s3(
    s3_client=s3_client,
    bucket_name=OUTPUT_S3_BUCKET,
    s3_folder=OUTPUT_S3_FOLDER,
    instance_id=instance_id,
)


json_data = get_json_file_from_s3(s3_client, OUTPUT_S3_BUCKET, benchmarking_file)
conn = load_dict_to_duckdb_using_read_json_auto(json_data, table_name="jd")
display(stacked_mem_cpu(conn, "jd", instance_id))
print_benchmark_info(json_data)
