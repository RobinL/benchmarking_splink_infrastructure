import time


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
