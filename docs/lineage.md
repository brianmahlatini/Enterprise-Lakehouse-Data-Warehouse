# Lineage

```mermaid
flowchart LR
  CSV[CSV extracts] --> Bronze
  API[JSON API events] --> Bronze
  DB[Relational entities] --> Bronze
  Bronze --> SilverCustomers[Silver customers]
  Bronze --> SilverProducts[Silver products]
  Bronze --> SilverTransactions[Silver transactions]
  Bronze --> SilverSupport[Silver support]
  Bronze --> SilverEvents[Silver events]
  SilverCustomers --> DimCustomer
  SilverProducts --> DimProduct
  SilverTransactions --> FactRevenue
  SilverSupport --> FactSupport
  SilverEvents --> FactEngagement
  DimCustomer --> Customer360
  FactRevenue --> Customer360
  FactSupport --> Customer360
  FactEngagement --> Customer360
  FactRevenue --> RevenueDaily
  Customer360 --> API
  RevenueDaily --> API
  API --> React
  API --> PowerBI[Power BI]
```

## Data Quality Rules

| Dataset | Business Key | Watermark | Quality Rules |
| --- | --- | --- | --- |
| customers | `customer_id` | `updated_at` | valid customer id and email |
| products | `product_id` | `updated_at` | non-negative price |
| transactions | `transaction_id` | `updated_at` | non-empty transaction id, positive quantity |
| support_events | `ticket_id` | `updated_at` | ticket and customer present |
| web_events | `event_id` | `updated_at` | event and customer present |

Rejected records are written to `data/lakehouse/quarantine/<dataset>`.
