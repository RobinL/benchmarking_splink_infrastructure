#!/bin/bash
set -e

# The sleep ensures that errors get logged before shutdown
trap "sleep 10; shutdown now" EXIT

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

# pip3 uninstall splink -y
# pip3 install splink==3.9.10

# python3 run.py \
#     --max_pairs "{max_pairs}" \
#     --num_input_rows "{num_input_rows}" \
#     --run_label "3.9.10" \
#     --output_bucket "{output_bucket}" \
#     --output_folder "{output_folder}" \
#     --aws_region "{aws_region}" 2>&1

pip3 uninstall splink -y


pip3 install -I git+https://github.com/robinl/splink.git@{tag_1}

python3 run.py \
    --max_pairs "{max_pairs}" \
    --num_input_rows "{num_input_rows}" \
    --run_label "{tag_1}" \
    --output_bucket "{output_bucket}" \
    --output_folder "{output_folder}" \
    --aws_region "{aws_region}" 2>&1


# pip3 uninstall splink -y


# pip3 install -I git+https://github.com/robinl/splink.git@{tag_2}

# python3 run.py \
#     --max_pairs "{max_pairs}" \
#     --num_input_rows "{num_input_rows}" \
#     --run_label "{tag_2}" \
#     --output_bucket "{output_bucket}" \
#     --output_folder "{output_folder}" \
#     --aws_region "{aws_region}" 2>&1


deactivate