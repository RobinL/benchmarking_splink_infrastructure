AWS_REGION = "eu-west-2"  # London
OUTPUT_S3_BUCKET = "robinsplinkbenchmarks"
OUTPUT_S3_FOLDER = "pytest_benchmark_results"
EC2_IAM_ROLE_NAME = "EC2S3RobinBenchmarksRole"
S3_IAM_POLICY_NAME = "S3AccessRobinSplinkBenchmarks"
CLOUDWATCH_IAM_POLICY_NAME = "CloudWatchAccessRobinSplinkBenchmarks"
EC2_IAM_INSTANCE_PROFILE_NAME = "EC2RobinBenchmarksInstanceProfile"

IMAGEID = "ami-05cae8d4948d6f5b7"  # arm64

INSTANCE_TYPE = "c6g.xlarge"  # arm64 4cpu 16gb $0.16/hr
# INSTANCE_TYPE = "c6g.2xlarge"
# INSTANCE_TYPE = "c6g.4xlarge"
# INSTANCE_TYPE = "c6g.16xlarge"  # arm64 64cpu 128gb $2.58/hr

# INSTANCE_TYPE = "c5.9xlarge"  # x86_64
# IMAGEID = "ami-0cfd0973db26b893b"  # x86_64


MAX_PAIRS = "1e5"
NUM_INPUT_ROWS = "1e3"
SPLINK_VARIANT_TAG_1 = "order_by_after_score"
SPLINK_VARIANT_TAG_2 = "order_by_after_union_all"
