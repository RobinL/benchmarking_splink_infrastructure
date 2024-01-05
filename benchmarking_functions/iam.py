import json

from botocore.exceptions import ClientError

from benchmarking_functions.constants import (
    CLOUDWATCH_IAM_POLICY_NAME,
    EC2_IAM_INSTANCE_PROFILE_NAME,
    EC2_IAM_ROLE_NAME,
    OUTPUT_S3_BUCKET,
    S3_IAM_POLICY_NAME,
)


# Function to clean up existing IAM resources
def cleanup_iam_resources(iam_client):
    # Detach and delete policies from the role
    try:
        attached_policies = iam_client.list_attached_role_policies(
            RoleName=EC2_IAM_ROLE_NAME
        )["AttachedPolicies"]
        for policy in attached_policies:
            iam_client.detach_role_policy(
                RoleName=EC2_IAM_ROLE_NAME, PolicyArn=policy["PolicyArn"]
            )
            iam_client.delete_policy(PolicyArn=policy["PolicyArn"])
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Remove role from instance profile and delete the profile
    try:
        iam_client.remove_role_from_instance_profile(
            InstanceProfileName=EC2_IAM_INSTANCE_PROFILE_NAME,
            RoleName=EC2_IAM_ROLE_NAME,
        )
        iam_client.delete_instance_profile(
            InstanceProfileName=EC2_IAM_INSTANCE_PROFILE_NAME
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Delete the role
    try:
        iam_client.delete_role(RoleName=EC2_IAM_ROLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    print("Cleanup complete: IAM role, policy, and instance profile have been deleted.")


def create_iam_role_that_can_be_assumed_by_ec2(iam_client):
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
        RoleName=EC2_IAM_ROLE_NAME, AssumeRolePolicyDocument=assume_role_policy_document
    )
    return role


def create_s3_policy_and_attach_to_role(iam_client):
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

    policy = iam_client.create_policy(
        PolicyName=S3_IAM_POLICY_NAME, PolicyDocument=json.dumps(bucket_policy)
    )
    iam_client.attach_role_policy(
        RoleName=EC2_IAM_ROLE_NAME, PolicyArn=policy["Policy"]["Arn"]
    )
    return policy


def create_coloudwatch_policy_and_attach_to_role(iam_client):
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
                    "cloudwatch:GetMetricData",
                    "cloudwatch:ListMetrics",
                    "cloudwatch:PutMetricData",
                    "ec2:DescribeTags",
                    "ec2:DescribeInstances",
                ],
                "Resource": "*",
            },
        ],
    }

    policy = iam_client.create_policy(
        PolicyName=CLOUDWATCH_IAM_POLICY_NAME,
        PolicyDocument=json.dumps(cloudwatch_policy),
    )
    iam_client.attach_role_policy(
        RoleName=EC2_IAM_ROLE_NAME, PolicyArn=policy["Policy"]["Arn"]
    )
    return policy


def create_ec2_instance_profile_and_attach_role(iam_client):
    iam_client.create_instance_profile(
        InstanceProfileName=EC2_IAM_INSTANCE_PROFILE_NAME
    )

    iam_client.add_role_to_instance_profile(
        InstanceProfileName=EC2_IAM_INSTANCE_PROFILE_NAME, RoleName=EC2_IAM_ROLE_NAME
    )


def create_all_iam_resources(iam_client):
    create_iam_role_that_can_be_assumed_by_ec2(iam_client)

    create_s3_policy_and_attach_to_role(
        iam_client,
    )

    create_coloudwatch_policy_and_attach_to_role(
        iam_client,
    )

    create_ec2_instance_profile_and_attach_role(
        iam_client,
    )
