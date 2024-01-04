import altair as alt


def mem_cpu_data(conn, df_name, instance_id):
    query = f"""
        with i1 as (
            SELECT
                jd.datetime,
                jd.custom.run_label as run_label,
                jd.custom.max_pairs as max_pairs,
                jd.benchmarks[1].name as benchmark_name,
                jd.benchmarks[1].stats.min as min_time,
                jd.benchmarks[1].stats.mean as mean_time,
                jd.machine_info.cpu.count as cpu_count,
                jd.machine_info.cpu.brand_raw as cpu_brand_raw,
                unnest(list_zip(
                    jd.custom.metrics.MetricDataResults[1].Timestamps,
                    jd.custom.metrics.MetricDataResults[1].Values,
                    jd.custom.metrics.MetricDataResults[2].Timestamps,
                    jd.custom.metrics.MetricDataResults[2].Values
                )) as zipped
            FROM {df_name}
            where jd.custom.instance_id = '{instance_id}'
        )
        select
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

    return conn.execute(query).df()


def stacked_mem_cpu(conn, df_name, instance_id):
    df = mem_cpu_data(conn, df_name, instance_id)

    mem_chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("mem_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),
            y="mem_value:Q",
            color=alt.value("blue"),
            tooltip=["datetime", "mem_value"],
        )
        .properties(title="Memory Usage Over Time", width=300, height=150)
    )

    cpu_chart = (
        alt.Chart(df)
        .mark_line()
        .encode(
            x=alt.X("cpu_timestamp:T", axis=alt.Axis(format="%H:%M:%S")),
            y="cpu_value:Q",
            color=alt.value("red"),
            tooltip=["datetime", "cpu_value"],
        )
        .properties(title="CPU Usage Over Time", width=300, height=150)
    )

    stacked_chart = alt.vconcat(mem_chart, cpu_chart).resolve_scale(
        x="shared", y="independent"
    )

    return stacked_chart
