from datetime import datetime, timedelta
from typing import List

import altair as alt
import boto3
import pandas as pd

from analysis_functions.duckdb_helpers import load_dicts_to_duckdb_using_read_json_auto
from analysis_functions.s3 import get_json_files_from_s3_prefix
from benchmarking_functions.constants import (
    AWS_REGION,
    OUTPUT_S3_FOLDER,
)

bar_chart_tooltip = [
    alt.Tooltip("mean_seconds:Q", title="Runtime (seconds)", format=".2f"),
    alt.Tooltip("max_pairs:Q", title="Max Pairs for estiamte u", format=","),
    alt.Tooltip("num_input_rows:Q", title="Number of Input Rows", format=","),
    alt.Tooltip("instance_type:N", title="Instance Type"),
    alt.Tooltip("vcpus:N", title="vCPUs"),
    alt.Tooltip("physical_processor:N", title="Physical Processor"),
    alt.Tooltip("clock_speed_ghz_:N", title="Clock Speed"),
    alt.Tooltip("instance_memory:N", title="Instance Memory"),
    alt.Tooltip("on_demand_price:N", title="On-Demand Price"),
]


benchmark_function_short_lookup = {
    "estimate_parameters_using_expectation_maximisation": "Estimate m",
    "estimate_probability_two_random_records_match": "Estimate λ",
    "estimate_u": "Estimate u",
    "predict": "Predict (inference)",
    "cluster": "Cluster",
}

CHART_WIDTH = 420


def load_instance_data(instances: List[str]):
    s3_client = boto3.client("s3", region_name=AWS_REGION)

    final_dict = {}
    for i in instances:
        dict_of_jsons = get_json_files_from_s3_prefix(
            s3_client, OUTPUT_S3_FOLDER + f"/statistics/benchmarking_results_{i}"
        )
        final_dict = {**final_dict, **dict_of_jsons}
    conn = load_dicts_to_duckdb_using_read_json_auto(final_dict, "df")

    instance_types = pd.read_csv("./analysis_functions/vantage_sh_instances.csv")

    instance_types.columns = instance_types.columns.str.replace(
        r"[ ()]", "_"
    ).str.lower()
    conn.register("instance_types", instance_types)

    return conn


def get_runtime_bar_chart_data(conn):
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
            WHEN benchmark_name LIKE '%cluster%' THEN 4
            ELSE 5
        END as benchmark_group1,

        CASE
            WHEN benchmark_name LIKE '%estimate_probability_two_rand%' THEN 'estimate_probability_two_random_records_match'
            WHEN benchmark_name LIKE '%estimate_u%' THEN 'estimate_u'
            WHEN benchmark_name LIKE '%estimate_parameters_using%' THEN 'estimate_parameters_using_expectation_maximisation'
            WHEN benchmark_name LIKE '%predict%' THEN 'predict'
            WHEN benchmark_name LIKE '%cluster%' THEN 'cluster'
            ELSE 4
        END as benchmark_function,



        from unnested),

        formatted as (
        select mean_seconds,
        benchmark_function,
        benchmark_group1,
        run_label,
        max_pairs,
        num_input_rows,
        count as num_cpus,
        instance_id,
        instance_type,
        brand_raw
        from grouped


        )

        select
            formatted.*,
            instance_types.vcpus,
            instance_types.physical_processor,
            instance_types.clock_speed_ghz_,
            instance_types.instance_memory,
            instance_types.on_demand as on_demand_price,

        from formatted left join instance_types on formatted.instance_type = instance_types.api_name
        ORDER BY benchmark_group1 asc, num_cpus, run_label
        """
    results_for_chart = conn.execute(query).df()
    results_for_chart["instance_desc"] = (
        results_for_chart["instance_type"]
        + " ("
        + results_for_chart["vcpus"].astype(str)
        + " "
        + results_for_chart["instance_memory"].astype(str)
        + ")"
    )

    return results_for_chart


def get_runtime_bar_chart(instances: list):
    conn = load_instance_data(instances)
    results_for_chart = get_runtime_bar_chart_data(conn)

    results_for_chart = results_for_chart.query("benchmark_function == 'predict'")
    results_for_chart["mean_minutes"] = results_for_chart["mean_seconds"] / 60
    chart = (
        alt.Chart(results_for_chart)
        .mark_bar()
        .encode(
            y=alt.Y(
                "instance_desc:N",
                sort=alt.EncodingSortField(field="num_cpus", order="descending"),
                axis=alt.Axis(title="EC2 Instance"),
            ),  # More descriptive y-axis title
            x=alt.X(
                "mean_minutes:Q", axis=alt.Axis(title="Runtime (minutes)")
            ),  # More descriptive x-axis title
            tooltip=bar_chart_tooltip,
        )
        .properties(
            title={
                "text": [
                    "Runtime for Splink inference (predict step) vs. machine spec"
                ],
                "subtitle": ["Hover over bars for details "],
                "color": "black",
                "subtitleColor": "gray",
            },
        )
    )
    return chart


def get_mem_cpu_charts(instances: list):
    conn = load_instance_data(instances)
    results_for_chart = get_runtime_bar_chart_data(conn)

    results_for_chart["benchmark_fn_short"] = results_for_chart[
        "benchmark_function"
    ].map(benchmark_function_short_lookup)

    results_for_chart["mean_minutes"] = results_for_chart["mean_seconds"] / 60

    query = """
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

            CAST(i1.zipped['list_1'] AS TIMESTAMP) as mem_timestamp,
            i1.zipped['list_2'] as mem_value,
            CAST(i1.zipped['list_3'] AS TIMESTAMP) as cpu_timestamp,
            i1.zipped['list_4'] as cpu_value,
            results_for_chart.instance_type
        from i1
        left join
        results_for_chart
        on i1.instance_id = results_for_chart.instance_id and
          benchmark_function='predict'


        """
    mem_cpu_data = conn.execute(query).df()

    click = alt.selection_point(encodings=["y"], value="c6i.32xlarge", empty=False)

    time_series_1 = (
        alt.Chart(mem_cpu_data)
        .mark_line()
        .encode(
            x=alt.X("mem_timestamp:T", title=None),
            y=alt.Y(
                "mem_value:Q", title="Memory Usage %", scale=alt.Scale(domain=[0, 100])
            ),
            tooltip=["mem_timestamp:T", "mem_value:Q", "mem_value:Q"],
        )
        .properties(width=CHART_WIDTH, height=150)
        .transform_filter(click)
    )

    time_series_2 = (
        alt.Chart(mem_cpu_data)
        .mark_line()
        .encode(
            x=alt.X("cpu_timestamp:T", title=None),
            y=alt.Y(
                "cpu_value:Q", title="CPU Usage %", scale=alt.Scale(domain=[0, 100])
            ),
            tooltip=["cpu_timestamp:T", "cpu_value:Q", "cpu_value:Q"],
        )
        .properties(width=CHART_WIDTH, height=150)
        .transform_filter(click)
    )

    bars = (
        alt.Chart(results_for_chart)
        .mark_bar()
        .encode(
            y=alt.Y(
                "instance_type:N",
                sort=alt.EncodingSortField(field="num_cpus", order="descending"),
                axis=alt.Axis(title="Instance id"),
            ),
            x=alt.X(
                "mean_minutes:Q",
                axis=alt.Axis(
                    title="Total runtime of training, inference and clustering (minutes)"
                ),
            ),
            color=alt.condition(
                click,
                alt.Color(
                    "benchmark_fn_short:N",
                    scale=alt.Scale(scheme="category20"),
                    sort=alt.EncodingSortField(
                        field="benchmark_group1", order="ascending"
                    ),
                ),
                alt.value("lightgray"),
            ),
            order=alt.Order("benchmark_group1:Q", sort="ascending"),
            tooltip=bar_chart_tooltip,
        )
        .properties(
            title={
                "text": ["CPU and Memory Usage for each run"],
                "subtitle": ["Click on bar to view corresponding memory and CPU usage"],
                "color": "black",
                "subtitleColor": "gray",
            },
            width=420,
        )
    ).add_params(click)
    bars

    chart = alt.vconcat(bars, time_series_1, time_series_2)
    return chart


def get_by_function_bar_chart(instances):
    conn = load_instance_data(instances)
    cdata = get_runtime_bar_chart_data(conn)

    cdata["benchmark_fn_short"] = cdata["benchmark_function"].map(
        benchmark_function_short_lookup
    )

    details_chart = (
        alt.Chart(
            cdata,
        )
        .mark_bar(size=10)
        .encode(
            y=alt.Y(
                "benchmark_fn_short:N",
                sort=alt.EncodingSortField(field="benchmark_group1", order="ascending"),
                axis=alt.Axis(title="Splink Function"),
            ),
            x=alt.X(
                "mean_seconds:Q",
                axis=alt.Axis(
                    title="Runtime (Seconds)",
                    values=[1, 5, 10, 25, 50, 100, 250, 500],
                ),
                scale=alt.Scale(type="symlog", constant=10),
            ),
            yOffset=alt.YOffset(
                "instance_type:N",
                sort=alt.EncodingSortField(field="num_cpus", order="descending"),
            ),
            color=alt.Color(
                "instance_type:N",
                sort=alt.EncodingSortField(field="num_cpus", order="descending"),
            ),
            tooltip=bar_chart_tooltip,
        )
        .properties(
            title={
                "text": ["Runtime by Splink Function"],
                "subtitle": ["Hover over bars for details"],
                "color": "black",
                "subtitleColor": "gray",
            },
            height=alt.Step(10),
            width=CHART_WIDTH,
        )
    )
    return details_chart
