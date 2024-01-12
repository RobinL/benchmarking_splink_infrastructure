import altair as alt
import boto3
import pandas as pd

from analysis_functions.duckdb_helpers import load_dicts_to_duckdb_using_read_json_auto
from analysis_functions.s3 import get_json_files_from_s3_prefix
from benchmarking_functions.constants import (
    AWS_REGION,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
)

s3_client = boto3.client("s3", region_name=AWS_REGION)

instances = [
    "i-0a544c96bb373cfa0",
    "i-0ae0b81108ec3c84d",
    "i-03cc8a3e708bea937",
    "i-056ebcd9cb91bc6ce",
    "i-08cc3110acd7b818b",
]

instance_types = pd.read_csv("./analysis_functions/vantage_sh_instances.csv")

instance_types.columns = instance_types.columns.str.replace(r"[ ()]", "_").str.lower()

instance_types

final_dict = {}
for i in instances:
    dict_of_jsons = get_json_files_from_s3_prefix(
        s3_client, OUTPUT_S3_FOLDER + f"/benchmarking_results_{i}"
    )
    final_dict = {**final_dict, **dict_of_jsons}
conn = load_dicts_to_duckdb_using_read_json_auto(final_dict, "df")

conn.execute("select * from df").df()


final_dict


query = """
with unnested as (
    SELECT
        unnest(benchmarks).name as benchmark_name,
        custom.run_label,

        custom.instance_id,


        custom.max_pairs,
        custom.num_input_rows,
        custom.instance_type,
        unnest(benchmarks).stats.mean as mean_seconds,
        machine_info.cpu.count,

        machine_info.cpu.brand_raw,


    FROM df
    ), grouped as(
    select * ,
    CASE
        WHEN benchmark_name LIKE '%estimate_probability_two_rand%' THEN 0
         WHEN benchmark_name LIKE '%estimate_u%' THEN 1
         WHEN benchmark_name LIKE '%estimate_parameters_using%' THEN 2
         WHEN benchmark_name LIKE '%predict%' THEN 3
         ELSE 4
    END as benchmark_group1,

    CASE
        WHEN benchmark_name LIKE '%estimate_probability_two_rand%' THEN 'estimate_probability_two_random_records_match'
         WHEN benchmark_name LIKE '%estimate_u%' THEN 'estimate_u'
         WHEN benchmark_name LIKE '%estimate_parameters_using%' THEN 'estimate_parameters_using_expectation_maximisation'
         WHEN benchmark_name LIKE '%predict%' THEN 'predict'
         ELSE 4
    END as benchmark_function,


    CASE
    WHEN benchmark_name LIKE '%no_salt%' THEN 0
        WHEN benchmark_name LIKE '%salt_2%' THEN 1
        WHEN benchmark_name LIKE '%cpu_salted%' THEN 2
        ELSE 3
    END as benchmark_group2,

    CASE
    WHEN benchmark_name LIKE '%no_salt%' THEN 'no_salt'
    WHEN benchmark_name LIKE '%salt_2%' THEN 'salt_2'
    WHEN benchmark_name LIKE '%cpu_salted%' THEN 'cpu_salted'
    END as salt_type

    from unnested),

    formatted as (

    select mean_seconds,
    benchmark_function,
    salt_type,
    run_label,
    max_pairs,
    num_input_rows,
    count as num_cpus,
    instance_id,
    instance_type,
    brand_raw
    from grouped
    where benchmark_function = 'predict' and salt_type = 'no_salt' and run_label = 'order_by_after_score'
    ORDER BY benchmark_group1, num_cpus,benchmark_group2, run_label

    )

    select
        formatted.*,
        instance_types.vcpus,
        instance_types.physical_processor,
        instance_types.clock_speed_ghz_,
        instance_types.instance_memory,
        instance_types.on_demand as on_demand_price,

      from formatted left join instance_types on formatted.instance_type = instance_types.api_name
    """
results_for_chart = conn.execute(query).df()


# new field that is the string concat of instance_type, vcpus and instance_memory
results_for_chart["instance_desc"] = (
    results_for_chart["instance_type"]
    + " ("
    + results_for_chart["vcpus"].astype(str)
    + " "
    + results_for_chart["instance_memory"].astype(str)
    + ")"
)

tooltip = [
    alt.Tooltip("mean_seconds:Q", title="Mean Runtime", format=".2f"),
    alt.Tooltip("max_pairs:Q", title="Max Pairs for estiamte u", format=","),
    alt.Tooltip("num_input_rows:Q", title="Number of Input Rows", format=","),
    alt.Tooltip("num_cpus:Q", title="Count", format=","),
    alt.Tooltip("instance_id:N", title="Instance ID"),
    alt.Tooltip("instance_type:N", title="Instance Type"),
    alt.Tooltip("vcpus:N", title="vCPUs"),
    alt.Tooltip("physical_processor:N", title="Physical Processor"),
    alt.Tooltip("clock_speed_ghz_:N", title="Clock Speed"),
    alt.Tooltip("instance_memory:N", title="Instance Memory"),
    alt.Tooltip("on_demand_price:N", title="On-Demand Price"),
]

chart = (
    alt.Chart(results_for_chart)
    .mark_bar()
    .encode(
        y=alt.Y(
            "instance_desc:N",
            sort=alt.EncodingSortField(field="num_cpus", order="descending"),
            axis=alt.Axis(title="Instance Description"),
        ),  # More descriptive y-axis title
        x=alt.X(
            "mean_seconds:Q", axis=alt.Axis(title="Runtime (Seconds)")
        ),  # More descriptive x-axis title
        tooltip=tooltip,
    )
    .properties(
        title={
            "text": ["Runtime to Find Matching Records"],
            "subtitle": ["Hover over bars for details "],
            "color": "black",
            "subtitleColor": "gray",
        },
    )
    .interactive()
)

# Display the chart
chart.save("runtime_chart.json")


# Now make interactive chart that allows analysis of memory and CPU usage

from datetime import datetime, timedelta

import altair as alt
import pandas as pd

query = f"""
    with i1 as (
        SELECT
            df.custom.instance_id,
            df.datetime,
            df.custom.run_label as run_label,
            df.custom.max_pairs as max_pairs,
            df.benchmarks[1].name as benchmark_name,
            df.benchmarks[1].stats.min as min_time,
            df.benchmarks[1].stats.mean as mean_time,
            df.machine_info.cpu.count as cpu_count,
            df.machine_info.cpu.brand_raw as cpu_brand_raw,
            unnest(list_zip(
                df.custom.metrics.MetricDataResults[1].Timestamps,
                df.custom.metrics.MetricDataResults[1].Values,
                df.custom.metrics.MetricDataResults[2].Timestamps,
                df.custom.metrics.MetricDataResults[2].Values
            )) as zipped
        FROM df

    )
    select
        instance_id,
        datetime,
        run_label,
        max_pairs,
        benchmark_name,
        min_time,
        mean_time,
        cpu_count,
        cpu_brand_raw,
        CAST(zipped['list_1'] AS TIMESTAMP) as mem_timestamp,
        zipped['list_2'] as mem_value,
        CAST(zipped['list_3'] AS TIMESTAMP) as cpu_timestamp,
        zipped['list_4'] as cpu_value
    from i1

    """
mem_cpu_data = conn.execute(query).df()


import altair as alt

click = alt.selection_point(encodings=["color"])


# Top panel is a time series plot of memory and CPU usage
time_series_1 = (
    alt.Chart(mem_cpu_data)
    .mark_line()
    .encode(
        x="mem_timestamp:T",
        y=alt.Y("mem_value:Q", title="Memory Usage"),
        color="instance_id:N",
        tooltip=["mem_timestamp:T", "mem_value:Q", "mem_value:Q"],
    )
    .properties(width=550, height=300)
    .transform_filter(click)
)
mem_cpu_data

results_for_chart
# Bottom panel is a bar chart of instance IDs and total runtime
# Updated Bottom panel as a bar chart of instance IDs and total runtime

bars = (
    alt.Chart(results_for_chart)
    .mark_bar()
    .encode(
        y=alt.Y(
            "instance_id:N",
            sort=alt.EncodingSortField(field="num_cpus", order="descending"),
            axis=alt.Axis(title="Instance id"),
        ),  # More descriptive y-axis title
        x=alt.X(
            "mean_seconds:Q", axis=alt.Axis(title="Runtime (Seconds)")
        ),  # More descriptive x-axis title
        color=alt.condition(click, "instance_id:N", alt.value("lightgray")),
        tooltip=tooltip,
    )
    .properties(
        title={
            "text": ["Runtime to Find Matching Records"],
            "subtitle": ["Hover over bars for details "],
            "color": "black",
            "subtitleColor": "gray",
        },
    )
    .add_params(click)
)
bars


# Combine the plots
chart = alt.vconcat(bars, time_series_1, title="Instance Usage and Runtime")

chart
