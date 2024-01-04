#!/bin/bash
set -e

trap "shutdown now" EXIT

yum update -y
yum install -y amazon-cloudwatch-agent python3-pip git at

systemctl start atd
echo "shutdown -h now" | at now + 2 hours


cd /home/ec2-user
git clone https://github.com/RobinL/run_splink_benchmarks_in_ec2.git

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/home/ec2-user/run_splink_benchmarks_in_ec2/metrics_config.json -s


cd run_splink_benchmarks_in_ec2
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# python3 run.py --max_pairs "1.1e8" --run_label "release" --output_bucket "robinsplinkbenchmarks"
pip3 uninstall splink -y
pip3 install -I git+https://github.com/moj-analytical-services/splink.git@faster_duckdb_for_benchmarking

python3 run.py --max_pairs "1.1e7" --run_label "faster_duckdb_for_benchmarking" --output_bucket "robinsplinkbenchmarks" --output_folder "pytest_benchmark_results"

deactivate