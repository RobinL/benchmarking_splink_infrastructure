import time

from benchmarking_functions.constants import (
    EC2_IAM_INSTANCE_PROFILE_NAME,
    IMAGEID,
    INSTANCE_TYPE,
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
    user_data_script = read_user_data_script(user_data_file_path)

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
