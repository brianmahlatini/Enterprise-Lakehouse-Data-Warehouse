"""Databricks entrypoint.

Upload this repo to Databricks Repos and run:
spark-submit pipelines/databricks_job.py --raw s3://bucket/raw --lake s3://bucket/lakehouse --warehouse s3://bucket/warehouse
"""

from lakehouse_pipeline import run

if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--lake", type=Path, required=True)
    parser.add_argument("--warehouse", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.raw, args.lake, args.warehouse), indent=2))
