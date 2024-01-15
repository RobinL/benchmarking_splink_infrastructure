import time
from datetime import datetime

import altair as alt
import boto3
from IPython.display import display

from analysis_functions.charts import stacked_mem_cpu
from analysis_functions.duckdb_helpers import load_dict_to_duckdb_using_read_json_auto
from analysis_functions.messages import print_benchmark_info, print_cloudwatch_link
from analysis_functions.s3 import get_json_file_from_s3
from benchmarking_functions.cloudwatch import (
    download_cloudwatch_log,
    get_metric_data_from_ec2_run,
)
from benchmarking_functions.constants import (
    AWS_REGION,
    SPLINK_VARIANT_TAG_1,
    SPLINK_VARIANT_TAG_2,
)
from benchmarking_functions.ec2 import poll_instance_id, run_instance_with_user_data
from benchmarking_functions.iam import cleanup_iam_resources, create_all_iam_resources
from benchmarking_functions.s3 import (
    create_bucket_if_not_exists,
    find_benchmarking_file_in_s3,
)

s3_client = boto3.client("s3", region_name=AWS_REGION)
iam_client = boto3.client("iam", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)
logs_client = boto3.client("logs", region_name=AWS_REGION)

start_time = time.time()

create_bucket_if_not_exists(s3_client)

cleanup_iam_resources(iam_client)

create_all_iam_resources(iam_client)

# Allow time for propogation delays
time.sleep(10)


metrics_collection_start_time = datetime.utcnow()


instance = run_instance_with_user_data(ec2_client, "user_data_clone_run_benchmarks.sh")

print_cloudwatch_link(instance)
time.sleep(5)
poll_instance_id(ec2_client, instance)

metrics_collection_end_time = datetime.utcnow()


metrics_response = get_metric_data_from_ec2_run(
    cw_client=cw_client,
    instance=instance,
    metrics_collection_start_time=metrics_collection_start_time,
    metrics_collection_end_time=metrics_collection_end_time,
)


cleanup_iam_resources(iam_client)

end_time = time.time()
print(f"Total time taken: {end_time - start_time:.2f} seconds")

# Print results
instance_id = instance["Instances"][0]["InstanceId"]
download_cloudwatch_log(logs_client, "SplinkBenchmarking", instance_id, "logs_folder")

# benchmarking_file = find_benchmarking_file_in_s3(
#     s3_client=s3_client,
#     instance_id=instance_id,
#     run_label="3.9.10",
# )


# json_data = get_json_file_from_s3(s3_client, benchmarking_file)
# conn = load_dict_to_duckdb_using_read_json_auto(json_data, table_name="jd")
# display(stacked_mem_cpu(conn, "jd", instance_id))
# print_benchmark_info(json_data)


benchmarking_file = find_benchmarking_file_in_s3(
    s3_client=s3_client,
    instance_id=instance_id,
    run_label=SPLINK_VARIANT_TAG_1,
)


json_data = get_json_file_from_s3(s3_client, benchmarking_file)
conn = load_dict_to_duckdb_using_read_json_auto(json_data, table_name="jd")
display(stacked_mem_cpu(conn, "jd", instance_id))
print_benchmark_info(json_data)

benchmarking_file = find_benchmarking_file_in_s3(
    s3_client=s3_client,
    instance_id=instance_id,
    run_label=SPLINK_VARIANT_TAG_2,
)


json_data = get_json_file_from_s3(s3_client, benchmarking_file)
conn = load_dict_to_duckdb_using_read_json_auto(json_data, table_name="jd")
display(stacked_mem_cpu(conn, "jd", instance_id))
print_benchmark_info(json_data)


con = load_dict_to_duckdb_using_read_json_auto(metrics_response, table_name="blah")
con.execute("select * from blah").df()

query = """
    with i1 as (
        SELECT

            unnest(list_zip(
                MetricDataResults[1].Timestamps,
                MetricDataResults[1].Values,
                MetricDataResults[2].Timestamps,
                MetricDataResults[2].Values
            )) as zipped
        FROM blah

    )
    select
        CAST(zipped['list_1'] AS TIMESTAMP) as mem_timestamp,
        zipped['list_2'] as mem_value,
        CAST(zipped['list_3'] AS TIMESTAMP) as cpu_timestamp,
        zipped['list_4'] as cpu_value
    from i1
    """

cpu_mem_data = con.execute(query).df()

mem_chart = (
    alt.Chart(cpu_mem_data)
    .mark_line()
    .encode(
        x=alt.X("mem_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),
        y="mem_value:Q",
        color=alt.value("blue"),
        tooltip=["mem_timestamp", "mem_value"],
    )
    .properties(title="Memory Usage Over Time", width=300, height=150)
)

cpu_chart = (
    alt.Chart(cpu_mem_data)
    .mark_line()
    .encode(
        x=alt.X("cpu_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),
        y="cpu_value:Q",
        color=alt.value("red"),
        tooltip=["cpu_timestamp", "cpu_value"],
    )
    .properties(title="CPU Usage Over Time", width=300, height=150)
)

stacked_chart = alt.vconcat(mem_chart, cpu_chart).resolve_scale(
    x="shared", y="independent"
)

stacked_chart
