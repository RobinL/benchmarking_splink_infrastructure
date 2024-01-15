import altair as alt

from analysis_functions.blog_charts import (
    bar_chart_tooltip,
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

instances = ["i-0e7d871d72b14817f", "i-03892923f5927093b"]

conn = load_instance_data(instances)
conn.execute("select * from df").df()

# query = """

# """
cdata = get_runtime_bar_chart_data(conn)


lookup = {
    "estimate_parameters_using_expectation_maximisation": "estimate_m",
    "estimate_probability_two_random_records_match": "estimate_λ",
    "estimate_u": "estimate_u",
    "predict": "predict",
}

cdata["benchmark_fn_short"] = cdata["benchmark_function"].map(lookup)


alt.Chart(cdata).mark_bar().encode(
    y=alt.Y(
        "benchmark_fn_short:N",
        sort=alt.EncodingSortField(field="benchmark_group1", order="ascending"),
    ),
    x="mean_seconds:Q",
    yOffset="instance_type:N",
    color="instance_type:N",
)

alt.Chart(cdata).mark_bar().encode(
    y=alt.Y(
        "benchmark_fn_short:N",
        sort=alt.EncodingSortField(field="benchmark_group1", order="ascending"),
        axis=alt.Axis(title="Splink Function"),
    ),
    x=alt.X("mean_seconds:Q", axis=alt.Axis(title="Mean Runtime (Seconds)")),
    yOffset=alt.YOffset(
        "instance_type:N",
    ),
    color="instance_type:N",
    tooltip=bar_chart_tooltip,
).properties(
    title={
        "text": ["Benchmark Function Runtime Analysis"],
        "subtitle": ["Hover over bars for details"],
        "color": "black",
        "subtitleColor": "gray",
    }
)
