AWS_REGION = "eu-west-2"  # London
OUTPUT_S3_BUCKET = "robinsplinkbenchmarks"
OUTPUT_S3_FOLDER = "pytest_benchmark_results"
EC2_IAM_ROLE_NAME = "EC2S3RobinBenchmarksRole"
S3_IAM_POLICY_NAME = "S3AccessRobinSplinkBenchmarks"
CLOUDWATCH_IAM_POLICY_NAME = "CloudWatchAccessRobinSplinkBenchmarks"
EC2_IAM_INSTANCE_PROFILE_NAME = "EC2RobinBenchmarksInstanceProfile"

IMAGEID = "ami-05cae8d4948d6f5b7"  # arm64

# INSTANCE_TYPE = "c6g.xlarge"  # arm64 4cpu 16gb $0.16/hr

# INSTANCE_TYPE = "c6gd.2xlarge"  # arm64 8cpu 16gb $0.36/hr with SSD
INSTANCE_TYPE = "c6g.4xlarge"  # arm64 16cpu 32gb $0.64/hr
# INSTANCE_TYPE = "c6g.8xlarge"  # arm64 32cpu 64gb $1.29/hr
# INSTANCE_TYPE = "c6g.16xlarge"  # arm64 64cpu 128gb $2.58/hr

# INSTANCE_TYPE = "c6i.32xlarge"  # x86_64 128cpu 256gb $6.46/hr
# IMAGEID = "ami-0cfd0973db26b893b"  # x86_64


MAX_PAIRS = "1e9"
NUM_INPUT_ROWS = "7e6"
# MAX_PAIRS = "1e7"
# NUM_INPUT_ROWS = "1.5e6"
SPLINK_VARIANT_TAG_1 = "3.9.11"
SPLINK_VARIANT_TAG_2 = "parallel_est_u_no_order_by"
