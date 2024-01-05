from benchmarking_functions.constants import (
    AWS_REGION,
    OUTPUT_S3_BUCKET,
    OUTPUT_S3_FOLDER,
)


def create_bucket_if_not_exists(s3_client):
    try:
        s3_client.create_bucket(
            Bucket=OUTPUT_S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
        )
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket '{OUTPUT_S3_BUCKET}' already exists in your account.")
    except s3_client.exceptions.BucketAlreadyExists:
        raise Exception(
            f"Bucket '{OUTPUT_S3_BUCKET}' already exists in another account."
        )


def find_benchmarking_file_in_s3(*, s3_client, instance_id):
    file_pattern = f"benchmarking_results_{instance_id}.json"

    prefix = f"{OUTPUT_S3_FOLDER}/{file_pattern}" if OUTPUT_S3_FOLDER else file_pattern

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=OUTPUT_S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(file_pattern):
                return key

    raise FileNotFoundError(
        f"No file found for '{file_pattern}' in '{OUTPUT_S3_BUCKET}/{OUTPUT_S3_FOLDER}'"
    )
