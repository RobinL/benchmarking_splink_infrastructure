#!/bin/bash
set -e

trap "shutdown now" EXIT

yum update -y
yum install -y amazon-cloudwatch-agent python3-pip git

cd /home/ec2-user
git clone https://github.com/RobinL/run_splink_benchmarks_in_ec2.git

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/home/ec2-user/test_run_benchmarks/metrics_config.json -s


cd run_splink_benchmarks_in_ec2
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 run.py
deactivate