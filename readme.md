## Benchmarking splink infrastructure

This repo creates and tears down the infrastructure needed for testing Splink

First change [the constants](benchmarking_functions/constants.py) to choose machine type and the name of the s3 bucket you want to use.

Then run [benchmark.py](benchmark.py)

Note that the Splink benchmarks themselves are in a [separate repo](https://github.com/robinl/run_splink_benchmarks_in_ec2).
