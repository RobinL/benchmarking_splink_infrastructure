import altair as alt
import duckdb

from analysis_functions.duckdb_helpers import load_dict_to_duckdb_using_read_json_auto


def get_metrics_chart(metrics_response):
    con = load_dict_to_duckdb_using_read_json_auto(metrics_response, table_name="blah")

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

    return stacked_chart
