import json
import time
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

OUTPUT_S3_BUCKET = "robinsplinkbenchmarks"
S3_IAM_ROLE_NAME = "EC2S3RobinBenchmarksRole"
S3_IAM_POLICY_NAME = "S3AccessRobinSplinkBenchmarks"
S3_IAM_INSTANCE_PROFILE_NAME = "EC2S3RobinBenchmarksInstanceProfile"
AWS_REGION = "eu-west-2"
# INSTANCE_TYPE = "c5.xlarge"  # x86_64
INSTANCE_TYPE = "c6gd.2xlarge"  # arm64 $0.31

# IMAGEID = "ami-0cfd0973db26b893b"  # x86_64
IMAGEID = "ami-05cae8d4948d6f5b7"  # arm64

# Initialize boto3 clients with London region
s3_client = boto3.client("s3", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)

start_time = time.time()

# Create S3 bucket
try:
    s3_client.create_bucket(
        Bucket=OUTPUT_S3_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
    )
except s3_client.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket '{OUTPUT_S3_BUCKET}' already exists in your account.")
except s3_client.exceptions.BucketAlreadyExists:
    raise Exception(f"Bucket '{OUTPUT_S3_BUCKET}' already exists in another account.")


# Function to clean up existing IAM resources
def cleanup_iam_resources():
    # Detach and delete policies from the role
    try:
        attached_policies = iam_client.list_attached_role_policies(
            RoleName=S3_IAM_ROLE_NAME
        )["AttachedPolicies"]
        for policy in attached_policies:
            iam_client.detach_role_policy(
                RoleName=S3_IAM_ROLE_NAME, PolicyArn=policy["PolicyArn"]
            )
            iam_client.delete_policy(PolicyArn=policy["PolicyArn"])
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Remove role from instance profile and delete the profile
    try:
        iam_client.remove_role_from_instance_profile(
            InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME, RoleName=S3_IAM_ROLE_NAME
        )
        iam_client.delete_instance_profile(
            InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Delete the role
    try:
        iam_client.delete_role(RoleName=S3_IAM_ROLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e


# Call the cleanup function at the beginning
cleanup_iam_resources()


# Create an IAM role for EC2
assume_role_policy_document = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
)

role = iam_client.create_role(
    RoleName=S3_IAM_ROLE_NAME, AssumeRolePolicyDocument=assume_role_policy_document
)

# Define a custom policy for accessing the specific S3 bucket
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
            ],
            "Resource": [
                f"arn:aws:s3:::{OUTPUT_S3_BUCKET}",
                f"arn:aws:s3:::{OUTPUT_S3_BUCKET}/*",
            ],
        }
    ],
}


s3_policy = iam_client.create_policy(
    PolicyName=S3_IAM_POLICY_NAME, PolicyDocument=json.dumps(bucket_policy)
)


iam_client.attach_role_policy(
    RoleName=S3_IAM_ROLE_NAME, PolicyArn=s3_policy["Policy"]["Arn"]
)

# Additional CloudWatch Logs policy
cloudwatch_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
            ],
            "Resource": ["arn:aws:logs:*:*:*"],
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "ec2:DescribeTags",
                "ec2:DescribeInstances",
            ],
            "Resource": "*",
        },
    ],
}


# Create and attach the CloudWatch policy
cw_policy = iam_client.create_policy(
    PolicyName="CloudWatchLogsPolicy", PolicyDocument=json.dumps(cloudwatch_policy)
)
iam_client.attach_role_policy(
    RoleName=S3_IAM_ROLE_NAME, PolicyArn=cw_policy["Policy"]["Arn"]
)


# Create an IAM instance profile
iam_client.create_instance_profile(InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME)

# Add the role to the instance profile
iam_client.add_role_to_instance_profile(
    InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME, RoleName=S3_IAM_ROLE_NAME
)

time.sleep(10)


# User data script with CloudWatch Agent installation and configuration
# Note that the instance seems to need to run for a while for it to actually log anything to
# the mem used - adding sleep 120 to the script made the mchine pop up in metrics


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
    IamInstanceProfile={"Name": S3_IAM_INSTANCE_PROFILE_NAME},
    InstanceInitiatedShutdownBehavior="terminate",
)

# Extract instance ID (for tracking or further operations if needed)
instance_id = instance["Instances"][0]["InstanceId"]


# Function to check instance state
def check_instance_state(ec2_client, instance_id):
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
    return state


# Polling loop to monitor instance state
while True:
    current_state = check_instance_state(ec2_client, instance_id)
    if current_state == "terminated":
        print(f"Instance {instance_id} has been terminated.")
        break
    elif current_state == "shutting-down":
        print(f"Instance {instance_id} is shutting down.")
    else:
        print(f"Instance {instance_id} is currently in state: {current_state}")

    time.sleep(5)  # Wait for 30 seconds before checking again

metrics_collection_end_time = datetime.utcnow()

metric_queries = [
    # Query for CPUUtilization
    {
        "Id": "ec2_cpu_utilization",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/EC2",
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
            },
            "Period": 5,
            "Stat": "Average",
        },
    },
    {
        "Id": "cw_agent_cpu_usage_user",
        "MetricStat": {
            "Metric": {
                "Namespace": "CWAgent",
                "MetricName": "cpu_usage_user",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
            },
            "Period": 5,
            "Stat": "Average",
        },
    },
    {
        "Id": "cw_agent_cpu_usage_system",
        "MetricStat": {
            "Metric": {
                "Namespace": "CWAgent",
                "MetricName": "cpu_usage_system",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
            },
            "Period": 5,
            "Stat": "Average",
        },
    },
    {
        "Id": "cw_agent_mem_used_percent",
        "MetricStat": {
            "Metric": {
                "Namespace": "CWAgent",
                "MetricName": "mem_used_percent",
                "Dimensions": [{"Name": "InstanceId", "Value": instance_id}],
            },
            "Period": 5,
            "Stat": "Average",
        },
    },
]


response = cw_client.get_metric_data(
    MetricDataQueries=metric_queries,
    StartTime=metrics_collection_start_time - timedelta(minutes=3),
    EndTime=metrics_collection_end_time + timedelta(minutes=3),
)
response


# Query parameters
metric_name = "mem_used_percent"
namespace = "CWAgent"  # Adjust if your metric is under a different namespace
dimensions = [
    {"Name": "InstanceId", "Value": instance_id},  # Replace with your instance ID
    {"Name": "InstanceType", "Value": INSTANCE_TYPE},  # Replace with your instance type
]

# Get metric data
response = cw_client.get_metric_data(
    MetricDataQueries=[
        {
            "Id": "query1",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": metric_name,
                    "Dimensions": dimensions,
                },
                "Period": 5,  # 5-second intervals
                "Stat": "Average",  # You can change this to 'Sum', 'Minimum', etc., as needed
            },
            "ReturnData": True,
        },
        {
            "Id": "query2",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": "cpu_usage_user",
                    "Dimensions": dimensions,
                },
                "Period": 5,  # 5-second intervals
                "Stat": "Average",  # You can change this to 'Sum', 'Minimum', etc., as needed
            },
            "ReturnData": True,
        },
    ],
    StartTime=metrics_collection_start_time,
    EndTime=metrics_collection_end_time,
)

# Process the response as needed

print(response)


# Write metrics data to a file
with open("metrics_data.json", "w") as file:
    json.dump(response, file, indent=4)


# Cleanup process

# Detach the S3 policy from the role
iam_client.detach_role_policy(
    RoleName=S3_IAM_ROLE_NAME, PolicyArn=s3_policy["Policy"]["Arn"]
)

# Delete the S3 policy
iam_client.delete_policy(PolicyArn=s3_policy["Policy"]["Arn"])

# Detach the CloudWatch Logs policy from the role
iam_client.detach_role_policy(
    RoleName=S3_IAM_ROLE_NAME, PolicyArn=cw_policy["Policy"]["Arn"]
)

# Delete the CloudWatch Logs policy
iam_client.delete_policy(PolicyArn=cw_policy["Policy"]["Arn"])

# Remove the role from the instance profile
iam_client.remove_role_from_instance_profile(
    InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME, RoleName=S3_IAM_ROLE_NAME
)

# Allow time for the role removal to propagate
time.sleep(10)

# Delete the IAM role
iam_client.delete_role(RoleName=S3_IAM_ROLE_NAME)

# Delete the IAM instance profile
iam_client.delete_instance_profile(InstanceProfileName=S3_IAM_INSTANCE_PROFILE_NAME)

print("Cleanup complete: IAM role, policy, and instance profile have been deleted.")

end_time = time.time()
print(f"Total time taken: {end_time - start_time:.2f} seconds")
