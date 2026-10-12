import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Database, Layers3, ShieldCheck } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getJson } from "./lib/api";
import "./styles.css";

function App() {
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [revenue, setRevenue] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getJson("/analytics/summary"),
      getJson("/metrics"),
      getJson("/analytics/revenue-daily"),
      getJson("/analytics/customer-360?limit=12"),
    ])
      .then(([summaryData, metricsData, revenueData, customerData]) => {
        setSummary(summaryData);
        setMetrics(metricsData);
        setRevenue(revenueData.slice(0, 24).reverse());
        setCustomers(customerData);
      })
      .catch((err) => setError(err.message));
  }, []);

  const tableMetrics = useMemo(() => Object.entries(metrics?.tables || {}), [metrics]);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Enterprise Lakehouse</p>
          <h1>Revenue Intelligence Platform</h1>
        </div>
        <div className="status"><Activity size={18} /> Spark, Delta, SQL, FastAPI, React</div>
      </header>

      {error && <section className="notice">Run `python scripts/generate_data.py` and `python pipelines/lakehouse_pipeline.py`, then refresh. {error}</section>}

      <section className="kpis">
        <article><Database /><span>Net Revenue</span><strong>${Number(summary?.net_revenue || 0).toLocaleString()}</strong></article>
        <article><Layers3 /><span>Customers</span><strong>{Number(summary?.customers || 0).toLocaleString()}</strong></article>
        <article><ShieldCheck /><span>High Risk</span><strong>{Number(summary?.high_risk_customers || 0).toLocaleString()}</strong></article>
        <article><Activity /><span>Pipeline Runtime</span><strong>{metrics?.runtime_seconds ?? "-"}s</strong></article>
      </section>

      <section className="grid">
        <div className="panel wide">
          <h2>Revenue by Day and Category</h2>
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={revenue}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d9dee8" />
              <XAxis dataKey="order_date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="net_revenue" fill="#2563eb" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Medallion Run Audit</h2>
          <div className="metric-list">
            {tableMetrics.map(([name, value]) => (
              <div key={name}>
                <span>{name}</span>
                <strong>{value.gold_rows ?? value.silver_rows ?? 0} rows</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Customer 360 Gold Mart</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Customer</th><th>Segment</th><th>Country</th><th>LTV</th><th>Orders</th><th>Risk</th></tr></thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.customer_id}>
                  <td>{c.full_name}</td><td>{c.segment}</td><td>{c.country}</td>
                  <td>${Number(c.lifetime_value || 0).toLocaleString()}</td><td>{c.orders}</td><td><span className={`risk ${c.retention_risk}`}>{c.retention_risk}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
