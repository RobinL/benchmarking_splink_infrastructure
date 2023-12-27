import time
from datetime import datetime

import boto3

from benchmarking_functions.cloudwatch import (
    get_metric_data_from_ec2_run,
    save_metrics_response_to_json,
)
from benchmarking_functions.constants import (
    AWS_REGION,
    CLOUDWATCH_IAM_POLICY_NAME,
    EC2_IAM_INSTANCE_PROFILE_NAME,
    EC2_IAM_ROLE_NAME,
    IMAGEID,
    INSTANCE_TYPE,
    OUTPUT_S3_BUCKET,
    S3_IAM_POLICY_NAME,
)
from benchmarking_functions.ec2 import poll_instance_id
from benchmarking_functions.iam import cleanup_iam_resources, create_all_iam_resources
from benchmarking_functions.s3 import create_bucket_if_not_exists

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


time.sleep(5)


def read_user_data_script(file_path):
    with open(file_path, "r") as file:
        return file.read()


user_data_file_path = "user_data_clone_run_benchmarks.sh"
user_data_script = read_user_data_script(user_data_file_path)

# The rest of your EC2 instance creation and monitoring code remains the same

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


save_metrics_response_to_json(response, "metrics_data.json")

cleanup_iam_resources(iam_client, EC2_IAM_ROLE_NAME, EC2_IAM_INSTANCE_PROFILE_NAME)

end_time = time.time()
print(f"Total time taken: {end_time - start_time:.2f} seconds")
