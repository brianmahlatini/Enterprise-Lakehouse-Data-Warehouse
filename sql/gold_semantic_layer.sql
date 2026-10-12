-- SQL endpoints can point to Delta tables on Databricks or the parquet warehouse locally.
create or replace view bi_revenue_daily as
select
  order_date,
  category,
  sum(net_revenue) as net_revenue,
  sum(orders) as orders
from gold.mart_revenue_daily
group by order_date, category;

create or replace view bi_customer_health as
select
  customer_id,
  full_name,
  segment,
  country,
  lifetime_value,
  orders,
  support_tickets,
  avg_csat,
  web_events,
  retention_risk
from gold.mart_customer_360;
