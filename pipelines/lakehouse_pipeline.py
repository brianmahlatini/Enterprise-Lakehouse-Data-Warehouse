from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F


TABLES = {
    "customers": {"format": "csv", "path": "customers.csv", "keys": ["customer_id"], "watermark": "updated_at"},
    "products": {"format": "csv", "path": "products.csv", "keys": ["product_id"], "watermark": "updated_at"},
    "transactions": {"format": "csv", "path": "transactions.csv", "keys": ["transaction_id"], "watermark": "updated_at"},
    "support_events": {"format": "csv", "path": "support_events.csv", "keys": ["ticket_id"], "watermark": "updated_at"},
    "web_events": {"format": "json", "path": "web_events.jsonl", "keys": ["event_id"], "watermark": "updated_at"},
}


def spark(app_name: str) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    )
    return builder.getOrCreate()


def read_raw(session: SparkSession, raw: Path, name: str) -> DataFrame:
    meta = TABLES[name]
    path = str(raw / meta["path"])
    if meta["format"] == "json":
        return session.read.json(path)
    return session.read.option("header", True).option("inferSchema", True).csv(path)


def write_table(df: DataFrame, base: Path, layer: str, name: str, mode: str = "overwrite") -> None:
    target = base / layer / name
    if os.name == "nt":
        if mode == "overwrite" and target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        rows = [row.asDict(recursive=True) for row in df.collect()]
        pq.write_table(pa.Table.from_pylist(rows), target / "part-00000.parquet")
        return
    df.write.mode(mode).format("parquet").save(str(target))


def write_parquet(df: DataFrame, target: Path) -> None:
    if os.name == "nt":
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        rows = [row.asDict(recursive=True) for row in df.collect()]
        pq.write_table(pa.Table.from_pylist(rows), target / "part-00000.parquet")
        return
    df.write.mode("overwrite").parquet(str(target))


def latest_per_key(df: DataFrame, keys: list[str], watermark: str) -> DataFrame:
    window = Window.partitionBy(*keys).orderBy(F.col(watermark).desc_nulls_last())
    return df.withColumn("_rn", F.row_number().over(window)).filter("_rn = 1").drop("_rn")


def clean_customers(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    typed = df.withColumn("updated_at", F.to_timestamp("updated_at")).withColumn("created_at", F.to_timestamp("created_at"))
    valid = F.col("customer_id").isNotNull() & F.col("email").rlike(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    return latest_per_key(typed.filter(valid), ["customer_id"], "updated_at"), typed.filter(~valid)


def clean_products(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    typed = df.withColumn("unit_price", F.col("unit_price").cast("double")).withColumn("updated_at", F.to_timestamp("updated_at"))
    valid = F.col("product_id").isNotNull() & (F.col("unit_price") >= 0)
    return latest_per_key(typed.filter(valid), ["product_id"], "updated_at"), typed.filter(~valid)


def clean_transactions(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    typed = (
        df.withColumn("quantity", F.col("quantity").cast("int"))
        .withColumn("unit_price", F.col("unit_price").cast("double"))
        .withColumn("discount_pct", F.col("discount_pct").cast("double"))
        .withColumn("occurred_at", F.to_timestamp("occurred_at"))
        .withColumn("updated_at", F.to_timestamp("updated_at"))
    )
    valid = F.col("transaction_id").isNotNull() & (F.length("transaction_id") > 0) & (F.col("quantity") > 0)
    return latest_per_key(typed.filter(valid), ["transaction_id"], "updated_at"), typed.filter(~valid)


def clean_support(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    typed = (
        df.withColumn("opened_at", F.to_timestamp("opened_at"))
        .withColumn("resolved_at", F.to_timestamp("resolved_at"))
        .withColumn("updated_at", F.to_timestamp("updated_at"))
        .withColumn("csat_score", F.col("csat_score").cast("int"))
    )
    valid = F.col("ticket_id").isNotNull() & F.col("customer_id").isNotNull()
    return latest_per_key(typed.filter(valid), ["ticket_id"], "updated_at"), typed.filter(~valid)


def clean_events(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    typed = df.withColumn("event_at", F.to_timestamp("event_at")).withColumn("updated_at", F.to_timestamp("updated_at"))
    valid = F.col("event_id").isNotNull() & F.col("customer_id").isNotNull()
    return latest_per_key(typed.filter(valid), ["event_id"], "updated_at"), typed.filter(~valid)


def build_gold(silver: dict[str, DataFrame]) -> dict[str, DataFrame]:
    customers = silver["customers"]
    products = silver["products"]
    transactions = silver["transactions"]
    support = silver["support_events"]
    events = silver["web_events"]

    dim_customer = customers.select("customer_id", "full_name", "email", "segment", "country", "signup_channel", "created_at")
    dim_product = products.select("product_id", "product_name", "category", "unit_price", "is_recurring")
    fact_revenue = (
        transactions.join(dim_product.select("product_id", "category"), "product_id", "left")
        .withColumn("gross_revenue", F.round(F.col("quantity") * F.col("unit_price"), 2))
        .withColumn("net_revenue", F.round(F.col("gross_revenue") * (1 - F.col("discount_pct")), 2))
        .withColumn("order_date", F.to_date("occurred_at"))
    )
    fact_support = support.withColumn("resolution_hours", F.round((F.unix_timestamp("resolved_at") - F.unix_timestamp("opened_at")) / 3600, 2))
    fact_engagement = events.withColumn("event_date", F.to_date("event_at"))
    mart_customer_360 = (
        dim_customer.alias("c")
        .join(fact_revenue.groupBy("customer_id").agg(F.sum("net_revenue").alias("lifetime_value"), F.count("*").alias("orders")), "customer_id", "left")
        .join(fact_support.groupBy("customer_id").agg(F.count("*").alias("support_tickets"), F.avg("csat_score").alias("avg_csat")), "customer_id", "left")
        .join(fact_engagement.groupBy("customer_id").agg(F.count("*").alias("web_events")), "customer_id", "left")
        .fillna({"lifetime_value": 0, "orders": 0, "support_tickets": 0, "web_events": 0})
        .withColumn("retention_risk", F.when((F.col("support_tickets") > 4) & (F.col("avg_csat") < 3), "high").otherwise("standard"))
    )
    revenue_daily = fact_revenue.groupBy("order_date", "category").agg(F.sum("net_revenue").alias("net_revenue"), F.count("*").alias("orders"))
    return {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "fact_revenue": fact_revenue,
        "fact_support": fact_support,
        "fact_engagement": fact_engagement,
        "mart_customer_360": mart_customer_360,
        "mart_revenue_daily": revenue_daily,
    }


def run(raw: Path, lake: Path, warehouse: Path) -> dict:
    session = spark("enterprise-lakehouse")
    started = time.perf_counter()
    metrics = {"tables": {}, "quality": {}, "layers": ["bronze", "silver", "gold"]}
    cleaners = {
        "customers": clean_customers,
        "products": clean_products,
        "transactions": clean_transactions,
        "support_events": clean_support,
        "web_events": clean_events,
    }

    silver = {}
    for name in TABLES:
        bronze = read_raw(session, raw, name).withColumn("_ingested_at", F.current_timestamp()).withColumn("_source_system", F.lit(TABLES[name]["format"]))
        write_table(bronze, lake, "bronze", name)
        clean, rejects = cleaners[name](bronze)
        write_table(clean, lake, "silver", name)
        write_table(rejects, lake, "quarantine", name)
        metrics["tables"][name] = {"bronze_rows": bronze.count(), "silver_rows": clean.count(), "rejected_rows": rejects.count()}
        metrics["quality"][name] = {"deduped_by": TABLES[name]["keys"], "watermark": TABLES[name]["watermark"]}
        silver[name] = clean

    gold = build_gold(silver)
    for name, df in gold.items():
        write_table(df, lake, "gold", name)
        write_parquet(df, warehouse / f"{name}.parquet")
        metrics["tables"][name] = {"gold_rows": df.count()}

    metrics["runtime_seconds"] = round(time.perf_counter() - started, 2)
    metrics["engine"] = "Apache Spark / PySpark local profile; same jobs run on Databricks with S3 paths."
    (lake / "_metadata").mkdir(parents=True, exist_ok=True)
    (lake / "_metadata" / "run_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    session.stop()
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--lake", type=Path, default=Path("data/lakehouse"))
    parser.add_argument("--warehouse", type=Path, default=Path("data/warehouse"))
    args = parser.parse_args()
    print(json.dumps(run(args.raw, args.lake, args.warehouse), indent=2))
