import json
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
                "Period": 5,
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
                "Period": 5,
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
