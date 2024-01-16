import altair as alt

from analysis_functions.blog_charts import (
    bar_chart_tooltip,
    get_by_function_bar_chart,
    get_mem_cpu_charts,
    get_runtime_bar_chart,
    get_runtime_bar_chart_data,
    load_instance_data,
)

# instances = [
#     "i-0a544c96bb373cfa0",
#     "i-0ae0b81108ec3c84d",
#     "i-03cc8a3e708bea937",
#     "i-056ebcd9cb91bc6ce",
#     "i-08cc3110acd7b818b",
# ]

# get_runtime_bar_chart(instances)
# get_mem_cpu_charts(instances)

# instances = ["i-0e7d871d72b14817f", "i-03892923f5927093b"]
alt.data_transformers.disable_max_rows()
# "i-0c0222021b987d985" is c6i.32xlarge with 2 salts per br
instances = [
    "i-0c0222021b987d985",
    "i-054f105e56d20ecda",
    "i-0bd2c095be044ac91",
    "i-01e30b0c645e362d5",
    "i-0f85be98655122cc7",
]


mem_cpu_chart = get_mem_cpu_charts(instances)
display(mem_cpu_chart)
mem_cpu_chart.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/cpu_mem_chart.vl.json"
)

runtime_bar = get_runtime_bar_chart(instances)
display(runtime_bar)
runtime_bar.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/summary_chart.vl.json"
)


by_function_chart = get_by_function_bar_chart(instances)
display(by_function_chart)
by_function_chart.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/by_function_chart.vl.json"
)


conn = load_instance_data(instances)
conn.execute("select * from df").df()

# query = """

# """


conn = load_instance_data(instances)
results_for_chart = get_runtime_bar_chart_data(conn)
results_for_chart


print(results_for_chart.head().to_markdown())
query = """
select sum(mean_seconds) as total_seconds

group by benchmark_function
from results_for_chart

"""

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
        i1.instance_id,
        i1.datetime,
        i1.run_label,
        i1.max_pairs,
        i1.benchmark_name,
        i1.min_time,
        i1.mean_time,
        i1.cpu_count,
        i1.cpu_brand_raw,
        CAST(i1.zipped['list_1'] AS TIMESTAMP) as mem_timestamp,
        i1.zipped['list_2'] as mem_value,
        CAST(i1.zipped['list_3'] AS TIMESTAMP) as cpu_timestamp,
        i1.zipped['list_4'] as cpu_value,
        results_for_chart.instance_type
    from i1
    left join
    results_for_chart
    on i1.instance_id = results_for_chart.instance_id


    """
mem_cpu_data = conn.execute(query).df()

click = alt.selection_point(encodings=["y"], value="c6g.2xlarge", empty=False)

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
    .properties(width=450, height=150)
    .transform_filter(click)
)

time_series_2 = (
    alt.Chart(mem_cpu_data)
    .mark_line()
    .encode(
        x=alt.X("cpu_timestamp:T", title=None),
        y=alt.Y("cpu_value:Q", title="CPU Usage %", scale=alt.Scale(domain=[0, 100])),
        tooltip=["cpu_timestamp:T", "cpu_value:Q", "cpu_value:Q"],
    )
    .properties(width=450, height=150)
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
        x=alt.X("mean_seconds:Q", axis=alt.Axis(title="Runtime (Seconds)")),
        color=alt.condition(
            click,
            alt.Color("benchmark_function:N", scale=alt.Scale(scheme="category20")),
            alt.value("lightgray"),
        ),
        tooltip=bar_chart_tooltip,
    )
    .properties(
        title={
            "text": ["CPU and Memory Usage for each run"],
            "subtitle": ["Click on bar to view corresponding memory and CPU usage"],
            "color": "black",
            "subtitleColor": "gray",
        },
        width=450,
    )
).add_params(click)
bars

chart = alt.vconcat(bars, time_series_1, time_series_2)
chart
