# Architecture

## Decision Summary

This project uses a medallion lakehouse because raw operational data, behavioral events and revenue facts need different levels of trust. Bronze preserves source fidelity for replay. Silver applies schema normalization, deduplication, CDC-style watermarks and data quality gates. Gold exposes dimensional facts, dimensions and BI-ready marts.

## Logical Flow

1. CSV, API-like JSONL and relational-style entities land in `data/raw`.
2. PySpark writes Bronze tables with ingestion metadata.
3. Silver tables keep the latest record per business key and quarantine invalid rows.
4. Gold builds `dim_customer`, `dim_product`, `fact_revenue`, `fact_support`, `fact_engagement`, `mart_customer_360` and `mart_revenue_daily`.
5. FastAPI serves curated analytics to React and BI tools.

## Cloud Mapping

Local paths map directly to cloud object storage:

| Local | AWS / Databricks |
| --- | --- |
| `data/raw` | `s3://<bucket>/raw` |
| `data/lakehouse/bronze` | Delta Bronze database |
| `data/lakehouse/silver` | Delta Silver database |
| `data/lakehouse/gold` | Delta Gold database |
| `data/warehouse` | SQL warehouse or Power BI import/direct query |

## Access Controls

Recommended production controls:

- S3 buckets encrypted with SSE-KMS and blocked public access.
- IAM roles scoped separately for ingestion, transformation and BI consumption.
- Databricks Unity Catalog grants by layer: engineers can read Bronze, analysts read Gold, service principals write pipeline outputs.
- Row filters or dynamic views for country or customer-specific data restrictions.

## Lineage

`docs/lineage.md` documents source-to-mart dependencies. `data/lakehouse/_metadata/run_metrics.json` records row counts, rejected records and runtime for each run.
