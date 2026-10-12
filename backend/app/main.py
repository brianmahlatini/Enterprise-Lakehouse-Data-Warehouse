from __future__ import annotations

import json
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings

app = FastAPI(title="Enterprise Lakehouse Analytics API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def parquet_path(table: str) -> Path:
    path = settings.warehouse_path / f"{table}.parquet"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{table} has not been built. Run the lakehouse pipeline first.")
    return path


def parquet_glob(path: Path) -> str:
    return str(path / "*.parquet") if path.is_dir() else str(path)


def query(sql: str, *paths: Path):
    con = duckdb.connect(database=":memory:")
    try:
        return con.execute(sql, [parquet_glob(path) for path in paths]).fetchall()
    finally:
        con.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "lakehouse-api"}


@app.get("/metrics")
def metrics():
    if not settings.metadata_path.exists():
        return {"runtime_seconds": None, "tables": {}, "quality": {}, "message": "Pipeline metrics not found yet."}
    return json.loads(settings.metadata_path.read_text(encoding="utf-8"))


@app.get("/analytics/revenue-daily")
def revenue_daily():
    path = parquet_path("mart_revenue_daily")
    rows = query(
        """
        select cast(order_date as varchar) as order_date, category, round(net_revenue, 2) as net_revenue, orders
        from read_parquet(?)
        order by order_date desc, category
        limit 120
        """,
        path,
    )
    return [{"order_date": r[0], "category": r[1], "net_revenue": r[2], "orders": r[3]} for r in rows]


@app.get("/analytics/customer-360")
def customer_360(limit: int = 25):
    path = parquet_path("mart_customer_360")
    rows = query(
        """
        select customer_id, full_name, segment, country, round(lifetime_value, 2), orders,
               support_tickets, round(avg_csat, 2), web_events, retention_risk
        from read_parquet(?)
        order by lifetime_value desc
        limit ?
        """.replace("limit ?", f"limit {max(1, min(limit, 100))}"),
        path,
    )
    return [
        {
            "customer_id": r[0],
            "full_name": r[1],
            "segment": r[2],
            "country": r[3],
            "lifetime_value": r[4],
            "orders": r[5],
            "support_tickets": r[6],
            "avg_csat": r[7],
            "web_events": r[8],
            "retention_risk": r[9],
        }
        for r in rows
    ]


@app.get("/analytics/summary")
def summary():
    revenue = parquet_path("fact_revenue")
    customers = parquet_path("mart_customer_360")
    rows = query(
        """
        select
          (select round(sum(net_revenue), 2) from read_parquet(?)) as net_revenue,
          (select count(*) from read_parquet(?)) as customers,
          (select count(*) from read_parquet(?) where retention_risk = 'high') as high_risk_customers
        """,
        revenue,
        customers,
        customers,
    )
    r = rows[0]
    return {"net_revenue": r[0], "customers": r[1], "high_risk_customers": r[2]}
