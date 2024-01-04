import json
import os
import tempfile

import duckdb


def load_dict_to_duckdb_using_read_json_auto(data_dict, table_name="df"):
    conn = duckdb.connect()

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as file:
        file.write(json.dumps(data_dict))
        temp_file_path = file.name

    try:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_json_auto('{temp_file_path}')"
        )

    finally:
        os.remove(temp_file_path)

    return conn


def load_dicts_to_duckdb_using_read_json_auto(data_dicts, table_name="df"):
    conn = duckdb.connect()

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        for s3_filename, value in data_dicts.items():
            file_path = os.path.join(temp_dir, s3_filename)
            print(s3_filename)
            with open(file_path, "w") as file:
                json.dump(value, file)

        # Load the entire directory into DuckDB
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_json_auto('{temp_dir}/*.json', filename=true)"
        )

    return conn
