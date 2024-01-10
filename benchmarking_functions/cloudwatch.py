import json
import os
from datetime import datetime

from benchmarking_functions.constants import (
    INSTANCE_TYPE,
)


def _create_metric_queries(instance_id, instance_type):
    dimensions = [
        {"Name": "InstanceId", "Value": instance_id},
        {
            "Name": "InstanceType",
            "Value": instance_type,
        },
    ]
    return [
        {
            "Id": "mem_used_query",
            "Label": f"{instance_id=} - {instance_type=} - Memory Used %",
            "MetricStat": {
                "Metric": {
                    "Namespace": "CWAgent",
                    "MetricName": "mem_used_percent",
                    "Dimensions": dimensions,
                },
                "Period": 1,
                "Stat": "Average",
            },
            "ReturnData": True,
        },
        {
            "Id": "user_cpu_used_query",
            "Label": f"{instance_id=} - {instance_type=} - CPU User %",
            "MetricStat": {
                "Metric": {
                    "Namespace": "CWAgent",
                    "MetricName": "cpu_usage_user",
                    "Dimensions": dimensions + [{"Name": "cpu", "Value": "cpu-total"}],
                },
                "Period": 1,
                "Stat": "Average",
            },
            "ReturnData": True,
        },
    ]


def _custom_json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_metric_data_from_ec2_run(
    *,
    cw_client,
    instance,
    metrics_collection_start_time,
    metrics_collection_end_time,
):
    instance_id = instance["Instances"][0]["InstanceId"]

    metric_queries = _create_metric_queries(instance_id, INSTANCE_TYPE)
    response = cw_client.get_metric_data(
        MetricDataQueries=metric_queries,
        StartTime=metrics_collection_start_time,
        EndTime=metrics_collection_end_time,
    )
    return response


def save_metrics_response_to_json(response, local_file_name):
    with open("metrics_data.json", "w") as file:
        json.dump(response, file, indent=4, default=_custom_json_serializer)


def download_cloudwatch_log(logs_client, log_group, log_stream, out_folder):
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    prev_token = None
    next_token = None
    all_log_events = []

    while True:
        if next_token:
            response = logs_client.get_log_events(
                logGroupName=log_group, logStreamName=log_stream, nextToken=next_token
            )
        else:
            response = logs_client.get_log_events(
                logGroupName=log_group, logStreamName=log_stream
            )

        all_log_events.extend(response["events"])

        prev_token = next_token
        next_token = response.get("nextForwardToken")

        # Check for end of stream
        if not next_token or next_token == prev_token:
            break

    # Define the file path including the output folder
    file_path = os.path.join(out_folder, f"{log_stream}.log")

    with open(file_path, "w") as file:
        for event in all_log_events:
            file.write(event["message"] + "\n")

    ap = os.path.abspath(file_path)

    print(f"Downloaded logs to file://{ap}")
