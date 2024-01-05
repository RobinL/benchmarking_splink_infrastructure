import json

from benchmarking_functions.constants import OUTPUT_S3_BUCKET


def get_json_file_from_s3(s3_client, bucket_name, file_key):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        json_content = response["Body"].read()
        return json.loads(json_content)
    except Exception as e:
        print(f"Error occurred while fetching JSON from S3: {e}")
        return None


def get_json_files_from_s3_prefix(s3_client, prefix):
    json_files = {}

    try:
        # List all objects with the specified prefix
        response = s3_client.list_objects_v2(Bucket=OUTPUT_S3_BUCKET, Prefix=prefix)
        if "Contents" in response:
            for item in response["Contents"]:
                file_key = item["Key"]

                if file_key.endswith(".json"):
                    file_content = s3_client.get_object(
                        Bucket=OUTPUT_S3_BUCKET, Key=file_key
                    )
                    json_content = file_content["Body"].read()
                    file_key = file_key.replace("/", "-")
                    json_files[file_key] = json.loads(json_content)

        return json_files

    except Exception as e:
        print(f"Error occurred while fetching JSON files from S3: {e}")
        return None
