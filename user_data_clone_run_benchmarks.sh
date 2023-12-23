#!/bin/bash
set -e

trap "shutdown now" EXIT

yum update -y
yum install -y amazon-cloudwatch-agent python3-pip git

cd /home/ec2-user
git clone https://github.com/RobinL/run_splink_benchmarks_in_ec2.git

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/home/ec2-user/run_splink_benchmarks_in_ec2/metrics_config.json -s


cd run_splink_benchmarks_in_ec2
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

python3 run.py --max_pairs "1e7" --run_label "release"
pip3 uninstall splink -y
pip3 install -I git+https://github.com/moj-analytical-services/splink.git@faster_duckdb

python3 run.py --max_pairs "1e7" --run_label "faster_duckdb"

deactivate