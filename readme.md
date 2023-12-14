To connect to the Ec2 instance using ec2 instance connect, have to go to security group and add an inbound rule to allow SSH traffic on port 22

https://instances.vantage.sh/


## Duckdb docs


https://duckdb.org/docs/guides/performance/my-workload-is-slow
> Do you have enough memory? DuckDB works best if you have 5-10GB memory per CPU core.

## Machine types

https://github.com/duckdblabs/db-benchmark/pull/54#issuecomment-1809941284

https://instances.vantage.sh/aws/ec2/c6id.metal

https://instances.vantage.sh/?min_memory=128&min_vcpus=48&min_storage=1000

## Comparison to macbook

>>>For your 2019 MacBook Pro with 6 cores and 12 threads, it's more accurate to compare it to 12 vCPUs in AWS terms. This is because AWS counts a vCPU as a single thread, not a full core. So, if your MacBook Pro has 6 physical cores and each core can run 2 threads (due to hyperthreading), it can be likened to an AWS instance with 12 vCPUs.
