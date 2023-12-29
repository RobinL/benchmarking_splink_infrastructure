import json

from botocore.exceptions import ClientError


# Function to clean up existing IAM resources
def cleanup_iam_resources(iam_client, role_name, instance_profile_name):
    # Detach and delete policies from the role
    try:
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)[
            "AttachedPolicies"
        ]
        for policy in attached_policies:
            iam_client.detach_role_policy(
                RoleName=role_name, PolicyArn=policy["PolicyArn"]
            )
            iam_client.delete_policy(PolicyArn=policy["PolicyArn"])
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Remove role from instance profile and delete the profile
    try:
        iam_client.remove_role_from_instance_profile(
            InstanceProfileName=instance_profile_name, RoleName=role_name
        )
        iam_client.delete_instance_profile(InstanceProfileName=instance_profile_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    # Delete the role
    try:
        iam_client.delete_role(RoleName=role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise e

    print("Cleanup complete: IAM role, policy, and instance profile have been deleted.")


def create_iam_role_that_can_be_assumed_by_ec2(iam_client, role_name):
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
        RoleName=role_name, AssumeRolePolicyDocument=assume_role_policy_document
    )
    return role


def create_s3_policy_and_attach_to_role(
    iam_client, role_name, policy_name, output_s3_bucket
):
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
                    f"arn:aws:s3:::{output_s3_bucket}",
                    f"arn:aws:s3:::{output_s3_bucket}/*",
                ],
            }
        ],
    }

    policy = iam_client.create_policy(
        PolicyName=policy_name, PolicyDocument=json.dumps(bucket_policy)
    )
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy["Policy"]["Arn"])
    return policy


def create_coloudwatch_policy_and_attach_to_role(iam_client, role_name, policy_name):
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
        PolicyName=policy_name, PolicyDocument=json.dumps(cloudwatch_policy)
    )
    iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy["Policy"]["Arn"])
    return policy


def create_ec2_instance_profile_and_attach_role(
    iam_client, instance_profile_name, role_name
):
    iam_client.create_instance_profile(InstanceProfileName=instance_profile_name)

    iam_client.add_role_to_instance_profile(
        InstanceProfileName=instance_profile_name, RoleName=role_name
    )


def create_all_iam_resources(
    iam_client,
    role_name,
    s3_policy_name,
    cloudwatch_policy_name,
    instance_profile_name,
    output_s3_bucket,
):
    create_iam_role_that_can_be_assumed_by_ec2(iam_client, role_name)

    create_s3_policy_and_attach_to_role(
        iam_client,
        role_name=role_name,
        policy_name=s3_policy_name,
        output_s3_bucket=output_s3_bucket,
    )

    create_coloudwatch_policy_and_attach_to_role(
        iam_client,
        role_name=role_name,
        policy_name=cloudwatch_policy_name,
    )

    create_ec2_instance_profile_and_attach_role(
        iam_client,
        instance_profile_name=instance_profile_name,
        role_name=role_name,
    )
