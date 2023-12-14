To connect to the Ec2 instance using ec2 instance connect, have to go to security group and add an inbound rule to allow SSH traffic on port 22

https://instances.vantage.sh/


## Duckdb docs


https://duckdb.org/docs/guides/performance/my-workload-is-slow
> Do you have enough memory? DuckDB works best if you have 5-10GB memory per CPU core.

## Machine types



Suitable families:

Start with:
https://instances.vantage.sh/aws/ec2/m6g.8xlarge

- 32 CPUs
- 128GB memory
- $1.42 an hour in London


https://instances.vantage.sh/aws/ec2/m6g.12xlarge at only $2.13 an hour 
- 48 cpus (24 core CPU 2 thread per cord)
- 192GB ram



This one's metal - other ones in the family should be ok too
https://instances.vantage.sh/aws/ec2/c6gd.metal
$2.90



If need Intel:
the following two families:
https://instances.vantage.sh/aws/ec2/m6id.8xlarge
https://instances.vantage.sh/aws/ec2/c6id.metal

The on duckdb uses is:
https://instances.vantage.sh/aws/ec2/c6id.metal
- 128 CPU
- 256GB memory

see [here](https://github.com/duckdblabs/db-benchmark/pull/54#issuecomment-1809941284)
## Comparison to macbook

>>>For your 2019 MacBook Pro with 6 cores and 12 threads, it's more accurate to compare it to 12 vCPUs in AWS terms. This is because AWS counts a vCPU as a single thread, not a full core. So, if your MacBook Pro has 6 physical cores and each core can run 2 threads (due to hyperthreading), it can be likened to an AWS instance with 12 vCPUs.
