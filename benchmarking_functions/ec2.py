import time

from benchmarking_functions.constants import (
    AWS_REGION,
    EC2_IAM_INSTANCE_PROFILE_NAME,
    IMAGEID,
    INSTANCE_TYPE,
    MAX_PAIRS,
    NUM_INPUT_ROWS,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
    SPLINK_VARIANT_TAG_1,
    SPLINK_VARIANT_TAG_2,
)


def read_user_data_script(file_path):
    with open(file_path, "r") as file:
        return file.read()


def _check_instance_state(ec2_client, instance):
    instance_id = instance["Instances"][0]["InstanceId"]
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
    return state


def poll_instance_id(ec2_client, instance):
    instance_id = instance["Instances"][0]["InstanceId"]
    while True:
        current_state = _check_instance_state(ec2_client, instance)
        if current_state == "terminated":
            print(f"Instance {instance_id} has been terminated.")
            break
        elif current_state == "shutting-down":
            print(f"Instance {instance_id} is shutting down.")
        else:
            print(f"Instance {instance_id} is currently in state: {current_state}")

        time.sleep(5)  # Wait for 30 seconds before checking again


def run_instance_with_user_data(ec2_client, user_data_file_path):
    user_data_script_template = read_user_data_script(user_data_file_path)

    interpolation_dict = {
        "max_pairs": MAX_PAIRS,
        "num_input_rows": NUM_INPUT_ROWS,
        "output_bucket": OUTPUT_S3_BUCKET,
        "output_folder": OUTPUT_S3_FOLDER,
        "aws_region": AWS_REGION,
        "tag_1": SPLINK_VARIANT_TAG_1,
        "tag_2": SPLINK_VARIANT_TAG_2,
    }

    user_data_script = user_data_script_template.format(**interpolation_dict)
    print(user_data_script)

    instance = ec2_client.run_instances(
        ImageId=IMAGEID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        UserData=user_data_script,
        IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE_NAME},
        InstanceInitiatedShutdownBehavior="terminate",
    )
    return instance
