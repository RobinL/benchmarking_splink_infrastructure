import json

import boto3


def create_bucket_if_not_exists(s3_client, bucket_name, region):
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket '{bucket_name}' already exists in your account.")
    except s3_client.exceptions.BucketAlreadyExists:
        raise Exception(f"Bucket '{bucket_name}' already exists in another account.")


def find_benchmarking_file_in_s3(*, s3_client, bucket_name, s3_folder, instance_id):
    # Construct the specific file name pattern
    file_pattern = f"benchmarking_results_{instance_id}.json"

    # Combine s3_folder and file_pattern to form the prefix
    prefix = f"{s3_folder}/{file_pattern}" if s3_folder else file_pattern

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(file_pattern):
                # Return the first match
                return key

    # Raise an error if no matching file is found
    raise FileNotFoundError(
        f"No file found for '{file_pattern}' in '{bucket_name}/{s3_folder}'"
    )


def get_json_file_from_s3(s3_client, bucket_name, file_key):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        json_content = response["Body"].read()
        return json.loads(json_content)
    except Exception as e:
        print(f"Error occurred while fetching JSON from S3: {e}")
        return None
