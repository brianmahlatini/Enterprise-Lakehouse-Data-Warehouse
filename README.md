# Enterprise Lakehouse & Data Warehouse

Senior data engineering platform for raw ingestion, medallion lakehouse processing, trusted dimensional modeling, analytics serving, BI reporting, lineage, and reproducible performance evidence.

This project turns an enterprise lakehouse brief into a portfolio-ready data platform with:

- Synthetic CSV, API-style JSONL, and relational-style source data
- PySpark medallion pipeline for Bronze, Silver, and Gold layers
- Delta Lake production design with a local Parquet execution profile
- Incremental-style deduplication using business keys and watermarks
- Data-quality quarantine for invalid source records
- Gold facts, dimensions, star-schema marts, and SQL semantic views
- FastAPI backend exposing analytical datasets
- React dashboard for revenue, customer health, and pipeline audit monitoring
- Docker Compose environment for local full-stack execution
- Databricks, AWS S3, lineage, access-control, and architecture documentation

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Cloud Lakehouse | Databricks, Delta Lake design, AWS S3 mapping |
| Distributed Processing | Apache Spark, PySpark, Spark SQL |
| Ingestion | Python, CSV, JSONL API-style events, relational-style extracts |
| Storage | Local Parquet profile, S3/Delta production target |
| Modeling | Bronze/Silver/Gold, facts, dimensions, star schemas |
| Backend API | Python, FastAPI, DuckDB, Pydantic Settings |
| Frontend | React, Vite, Recharts, Lucide React, CSS |
| BI | SQL semantic views, Power BI-ready datasets |
| DevOps | Docker, Docker Compose, Makefile |
| Documentation | Markdown, Mermaid lineage, SQL references |

## Architecture

```text
CSV + API JSONL + Relational Extracts
          |
          v
Bronze raw lakehouse tables
          |
          v
Silver cleansing, typing, deduplication, and quality quarantine
          |
          v
Gold facts, dimensions, customer 360, and revenue marts
          |
          +-----------> Databricks SQL / Power BI semantic views
          |
          v
FastAPI analytics service
          |
          v
React revenue intelligence dashboard
```

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   `-- settings.py
|   |-- tests/
|   |   |-- conftest.py
|   |   `-- test_api.py
|   |-- __init__.py
|   `-- Dockerfile
|-- data/
|   |-- raw/
|   |-- warehouse/
|   `-- lakehouse/
|-- docs/
|   |-- architecture.md
|   |-- databricks_aws.md
|   `-- lineage.md
|-- frontend/
|   |-- src/
|   |   |-- lib/api.js
|   |   |-- main.jsx
|   |   `-- styles.css
|   |-- Dockerfile
|   |-- index.html
|   |-- package-lock.json
|   `-- package.json
|-- pipelines/
|   |-- databricks_job.py
|   `-- lakehouse_pipeline.py
|-- scripts/
|   `-- generate_data.py
|-- sql/
|   `-- gold_semantic_layer.sql
|-- .gitignore
|-- docker-compose.yml
|-- Makefile
|-- README.md
`-- requirements.txt
```

## Business Questions Answered

- Which customers produce the highest lifetime value?
- Which customers show elevated retention risk based on support and satisfaction signals?
- How is revenue trending by day and product category?
- Which product categories drive the most orders and net revenue?
- How many source records were rejected by data-quality rules?
- Are Bronze, Silver, and Gold row counts auditable for each run?
- Which curated datasets should Power BI use for executive reporting?

## Metrics

| Metric | Definition |
| --- | --- |
| Net Revenue | Quantity multiplied by unit price after discount |
| Lifetime Value | Sum of net revenue by customer |
| Orders | Count of valid revenue transactions |
| Support Tickets | Count of support records by customer |
| Average CSAT | Average customer satisfaction score |
| Web Events | Count of engagement events by customer |
| Retention Risk | High when support volume is high and CSAT is low |
| Rejected Rows | Records failing Silver quality rules |
| Pipeline Runtime | End-to-end Spark job runtime in seconds |

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate deterministic source data:

```bash
python scripts/generate_data.py --scale 2 --output data/raw
```

Run the lakehouse pipeline:

```bash
python pipelines/lakehouse_pipeline.py --raw data/raw --lake data/lakehouse --warehouse data/warehouse
```

Start the API:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Start the React dashboard:

```bash
cd frontend
npm install
npm run dev
```

Services:

- React dashboard: `http://localhost:5173`
- FastAPI docs: `http://localhost:8000/docs`
- API health check: `http://localhost:8000/health`

## Run With Docker

Generate data and build the curated warehouse first:

```bash
python scripts/generate_data.py --scale 2 --output data/raw
python pipelines/lakehouse_pipeline.py --raw data/raw --lake data/lakehouse --warehouse data/warehouse
```

Start the full stack:

```bash
docker compose up --build
```

Services:

- React dashboard: `http://localhost:5173`
- FastAPI docs: `http://localhost:8000/docs`

Stop the stack:

```bash
docker compose down
```

## API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health check |
| `GET /metrics` | Pipeline runtime, row counts, and quality metadata |
| `GET /analytics/summary` | Executive revenue, customer, and risk KPIs |
| `GET /analytics/revenue-daily` | Daily revenue mart for charting and BI |
| `GET /analytics/customer-360` | Customer health, LTV, engagement, and risk mart |

## React Dashboard

The dashboard includes:

- KPI cards for net revenue, customers, high-risk customers, and pipeline runtime
- Revenue trend bar chart from the Gold revenue mart
- Medallion run audit panel with row counts by table
- Customer 360 table with segment, country, LTV, orders, and risk status
- API-driven data loading from the FastAPI analytical endpoints

## Lakehouse Layers

| Layer | Purpose |
| --- | --- |
| Bronze | Preserve source records with ingestion metadata |
| Silver | Type, clean, deduplicate, watermark, and quarantine invalid records |
| Gold | Publish dimensional facts, dimensions, and BI-ready marts |

Gold datasets:

- `dim_customer`
- `dim_product`
- `fact_revenue`
- `fact_support`
- `fact_engagement`
- `mart_customer_360`
- `mart_revenue_daily`

## Data Quality and Incremental Strategy

Each Silver table uses a business key and `updated_at` watermark to keep the latest source version:

| Dataset | Business Key | Watermark | Quality Rules |
| --- | --- | --- | --- |
| customers | `customer_id` | `updated_at` | valid customer id and email |
| products | `product_id` | `updated_at` | non-negative price |
| transactions | `transaction_id` | `updated_at` | non-empty transaction id and positive quantity |
| support_events | `ticket_id` | `updated_at` | ticket and customer present |
| web_events | `event_id` | `updated_at` | event and customer present |

Rejected records are written to:

```text
data/lakehouse/quarantine/<dataset>
```

## Generate Synthetic Data

Use the generator when you want a different data volume or repeatable benchmark:

```bash
python scripts/generate_data.py --scale 10 --seed 99 --output data/raw
```

Generated outputs:

- `data/raw/customers.csv`
- `data/raw/products.csv`
- `data/raw/transactions.csv`
- `data/raw/support_events.csv`
- `data/raw/web_events.jsonl`
- `data/raw/manifest.json`

The generator intentionally includes duplicate and invalid records to demonstrate deduplication, data-quality checks, and quarantine handling.

## Benchmarking

The pipeline writes run evidence to:

```text
data/lakehouse/_metadata/run_metrics.json
```

Example local run at `--scale 2`:

| Table | Rows |
| --- | ---: |
| Bronze customers | 701 |
| Silver customers | 700 |
| Bronze transactions | 10041 |
| Silver transactions | 10000 |
| Gold fact_revenue | 10000 |
| Gold fact_engagement | 14000 |
| Gold mart_customer_360 | 700 |
| Gold mart_revenue_daily | 2146 |

Example runtime:

```text
38.93 seconds
```

## SQL Analytics

BI-facing SQL lives in:

```text
sql/gold_semantic_layer.sql
```

Key semantic views:

- `bi_revenue_daily`
- `bi_customer_health`

These views are designed for Databricks SQL and Power BI, while the local API reads the same curated Gold outputs from Parquet.

## Databricks and AWS S3 Deployment

Local paths map to production cloud storage:

| Local Path | Production Target |
| --- | --- |
| `data/raw` | `s3://<bucket>/raw` |
| `data/lakehouse/bronze` | Delta Bronze tables |
| `data/lakehouse/silver` | Delta Silver tables |
| `data/lakehouse/gold` | Delta Gold tables |
| `data/warehouse` | Databricks SQL warehouse / Power BI serving layer |

Run on Databricks:

```bash
spark-submit pipelines/databricks_job.py \
  --raw s3://enterprise-lakehouse/raw \
  --lake s3://enterprise-lakehouse/lakehouse \
  --warehouse s3://enterprise-lakehouse/warehouse
```

Delta Lake is the production target because it provides ACID transactions, schema enforcement, time travel, and reliable merge/upsert support on cloud object storage.

## Power BI Build Guide

Open Power BI Desktop.

1. Select Get Data.
2. Choose the Databricks connector.
3. Connect to the Databricks SQL warehouse.
4. Import Gold tables or semantic views from `sql/gold_semantic_layer.sql`.
5. Build report pages:
   - Executive Revenue Overview
   - Customer 360 and Retention Risk
   - Product Category Revenue
   - Pipeline Quality and Rejected Records
   - Lakehouse Run Audit

Suggested visuals:

- KPI cards for net revenue, customers, high-risk customers, and runtime
- Bar chart for daily revenue by category
- Matrix for customer segment by country
- Table for customer health and retention risk
- Audit table for Bronze, Silver, Gold row counts

## Portfolio Narrative

Recommended CV wording:

Built a Dockerized Enterprise Lakehouse and Data Warehouse platform using Databricks-style medallion architecture, PySpark, Apache Spark, Delta Lake design patterns, AWS S3 deployment mapping, FastAPI, React, SQL, and Power BI-ready semantic views. Developed reproducible synthetic ingestion data, Bronze/Silver/Gold transformations, deduplication, incremental watermarks, data-quality quarantine, dimensional Gold marts, API serving, and a management dashboard for revenue intelligence and customer health analytics.

Evidence to include:

- Screenshot of React dashboard
- Screenshot of FastAPI `/docs`
- Pipeline metrics from `data/lakehouse/_metadata/run_metrics.json`
- SQL semantic views in `sql/gold_semantic_layer.sql`
- Lineage diagram from `docs/lineage.md`
- Databricks/S3 deployment notes from `docs/databricks_aws.md`
- Synthetic data generator command and benchmark output

## Senior-Level Design Notes

- The medallion design separates replayable raw data from trusted BI-serving datasets.
- Business-key deduplication and watermarks make transformations reproducible and incrementally oriented.
- Quality failures are quarantined instead of silently dropped.
- Gold tables follow dimensional modeling patterns so analysts can consume stable facts and dimensions.
- API and BI outputs read curated Gold data, keeping business metrics consistent across tools.
- Runtime and row-count metrics provide benchmark evidence for portfolio review.
- Databricks and S3 mappings show how the local project becomes a production cloud lakehouse.
- Access-control recommendations are documented for IAM, Unity Catalog, encryption, and BI consumption.

## Next Enhancements

- Add real Delta Lake writes for a Databricks integration test profile.
- Add dbt models and tests for Gold semantic transformations.
- Add Great Expectations or Deequ checks for richer data-quality validation.
- Add GitHub Actions for backend tests and frontend builds.
- Add a published Power BI `.pbix` report once screenshots are finalized.
- Add streaming ingestion with Auto Loader or Structured Streaming.
