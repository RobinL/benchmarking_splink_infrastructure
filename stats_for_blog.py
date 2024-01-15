from analysis_functions.blog_charts import (
    get_mem_cpu_charts,
    get_runtime_bar_chart,
)

instances = [
    "i-0a544c96bb373cfa0",
    "i-0ae0b81108ec3c84d",
    "i-03cc8a3e708bea937",
    "i-056ebcd9cb91bc6ce",
    "i-08cc3110acd7b818b",
]

get_runtime_bar_chart(instances)
get_mem_cpu_charts(instances)
