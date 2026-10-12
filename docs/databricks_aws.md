# Databricks and AWS Deployment

## Databricks Job

1. Create an S3 bucket with `raw`, `lakehouse` and `warehouse` prefixes.
2. Configure an instance profile or Unity Catalog external location for that bucket.
3. Attach a cluster with Spark 3.5 and Delta Lake support.
4. Run:

```bash
spark-submit pipelines/databricks_job.py \
  --raw s3://enterprise-lakehouse/raw \
  --lake s3://enterprise-lakehouse/lakehouse \
  --warehouse s3://enterprise-lakehouse/warehouse
```

## Why Delta Lake

Delta Lake is the production target because it adds ACID transactions, schema enforcement, time travel, merge/upsert support and reliable incremental processing on top of object storage. The local profile writes Parquet so the project runs without a Databricks cluster; the same table boundaries and transformations are designed for Delta tables in Databricks.

## BI Layer

Power BI can consume:

- Databricks SQL views from `sql/gold_semantic_layer.sql`.
- FastAPI endpoints for lightweight portfolio demos.
- Exported parquet files from `data/warehouse` for local inspection.
