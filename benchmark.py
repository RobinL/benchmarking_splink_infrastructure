import json
import time

import boto3

OUTPUT_S3_BUCKET = "robinsplinkbenchmarks"
S3_IAM_ROLE_NAME = "EC2S3RobinBenchmarksRole"
S3_IAM_POLICY_NAME = "S3AccessRobinSplinkBenchmarks"
S3_IAM_INSTANCE_PROFILE_NAME = "EC2S3RobinBenchmarksInstanceProfile"
AWS_REGION = "eu-west-2"
INSTANCE_TYPE = "c5.xlarge"

# Initialize boto3 clients with London region
s3_client = boto3.client("s3", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)

start_time = time.time()

# Create S3 bucket
try:
    s3_client.create_bucket(
        Bucket=OUTPUT_S3_BUCKET,
        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
    )
except s3_client.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket '{OUTPUT_S3_BUCKET}' already exists in yo2ur account.")
except s3_client.exceptions.BucketAlreadyExists:
    raise Exception(f"Bucket '{OUTPUT_S3_BUCKET}' already exists in another account.")

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


user_data_script = """#!/bin/bash
set -e

trap "shutdown now" EXIT

yum update -y
yum install -y amazon-cloudwatch-agent python3-pip git

cd /home/ec2-user
git clone -b pytest_benchmark https://github.com/RobinL/test_run_benchmarks.git

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/home/ec2-user/test_run_benchmarks/metrics_config.json -s

cd test_run_benchmarks
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 run.py

"""


instance = ec2_client.run_instances(
    ImageId="ami-0cfd0973db26b893b",  # Replace with your AMI ID
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
