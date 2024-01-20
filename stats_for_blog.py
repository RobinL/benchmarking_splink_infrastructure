import altair as alt

from analysis_functions.blog_charts import (
    bar_chart_tooltip,
    get_by_function_bar_chart,
    get_mem_cpu_charts,
    get_runtime_bar_chart,
    get_runtime_bar_chart_data,
    load_instance_data,
    spark_vs_duckdb_chart,
)

spark_vs_duckdb = spark_vs_duckdb_chart()
display(spark_vs_duckdb)
spark_vs_duckdb.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/spark_vs_duckdb_chart.vl.json"
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


by_function_chart = get_by_function_bar_chart(instances)
display(by_function_chart)
by_function_chart.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/by_function_chart.vl.json"
)


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

spark_vs_duckdb = spark_vs_duckdb_chart()
display(spark_vs_duckdb)
spark_vs_duckdb.save(
    "/Users/robinlinacre/Documents/personal/robinl.github.io/src/mdx_dev/fast_deduplication/spark_vs_duckdb_chart.vl.json"
)
