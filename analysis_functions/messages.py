def print_benchmark_info(json_data):
    benchmarks = json_data.get("benchmarks", [])
    custom_info = json_data.get("custom", {})

    labels = ["Benchmark:", "Mean:", "Max Pairs:", "Instance Type:", "Run Label:"]
    max_label_length = max(len(label) for label in labels)

    for benchmark in benchmarks:
        name = benchmark.get("fullname", "N/A")
        stats = benchmark.get("stats", {})
        mean = stats.get("mean", "N/A")
        max_pairs = custom_info.get("max_pairs", "N/A")
        instance_type = custom_info.get("instance_type", "N/A")
        run_label = custom_info.get("run_label", "N/A")

        print(f"{'Benchmark:'.ljust(max_label_length)} {name}")
        print(f"{'Mean:'.ljust(max_label_length)} {mean:.2f} seconds")
        print(f"{'Max Pairs:'.ljust(max_label_length)} {max_pairs}")
        print(f"{'Instance Type:'.ljust(max_label_length)} {instance_type}")
        print(f"{'Run Label:'.ljust(max_label_length)} {run_label}")


def print_cloudwatch_link(instance):
    instance_id = instance["Instances"][0]["InstanceId"]
    url = (
        "https://eu-west-2.console.aws.amazon.com/cloudwatch/home"
        "?region=eu-west-2#logsV2:log-groups/log-group/"
        f"SplinkBenchmarking/log-events/{instance_id}"
    )
    print(url)
