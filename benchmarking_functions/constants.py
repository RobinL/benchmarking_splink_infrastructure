AWS_REGION = "eu-west-2"  # London
OUTPUT_S3_BUCKET = "robinsplinkbenchmarks"
OUTPUT_S3_FOLDER = "pytest_benchmark_results"
EC2_IAM_ROLE_NAME = "EC2S3RobinBenchmarksRole"
S3_IAM_POLICY_NAME = "S3AccessRobinSplinkBenchmarks"
CLOUDWATCH_IAM_POLICY_NAME = "CloudWatchAccessRobinSplinkBenchmarks"
EC2_IAM_INSTANCE_PROFILE_NAME = "EC2RobinBenchmarksInstanceProfile"

IMAGEID = "ami-05cae8d4948d6f5b7"  # arm64
INSTANCE_TYPE = "c6g.xlarge"  # arm64

# INSTANCE_TYPE = "c5.xlarge"  # x86_64
# IMAGEID = "ami-0cfd0973db26b893b"  # x86_64
