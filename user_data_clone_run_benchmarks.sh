#!/bin/bash
set -e

# The sleep ensures that errors get logged before shutdown
trap "sleep 10; shutdown now" EXIT

yum update -y
yum install -y amazon-cloudwatch-agent python3-pip git at


systemctl start atd
echo "shutdown -h now" | at now + 4 hours



cd /home/ec2-user
git clone https://github.com/RobinL/run_splink_benchmarks_in_ec2.git

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/home/ec2-user/run_splink_benchmarks_in_ec2/metrics_config.json -s


yum install -y java-1.8.0-amazon-corretto

JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export JAVA_HOME
echo "export JAVA_HOME=$JAVA_HOME" >> /home/ec2-user/.bashrc


cd run_splink_benchmarks_in_ec2
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt


python3 run.py \
    --max_pairs "{max_pairs}" \
    --num_input_rows "{num_input_rows}" \
    --run_label "3.9.11" \
    --output_bucket "{output_bucket}" \
    --output_folder "{output_folder}" \
    --aws_region "{aws_region}" 2>&1


deactivate