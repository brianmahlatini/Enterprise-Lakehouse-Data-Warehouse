from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker


DATASETS = ("customers", "products", "transactions", "support_events", "web_events")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate(seed: int, scale: int, output: Path) -> None:
    fake = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)
    now = datetime(2026, 10, 12, tzinfo=timezone.utc)

    customer_count = 350 * scale
    product_count = 40 * scale
    transaction_count = 5000 * scale
    support_count = 900 * scale
    event_count = 7000 * scale

    customers = []
    for idx in range(1, customer_count + 1):
        created_at = now - timedelta(days=rng.randint(30, 900))
        customers.append(
            {
                "customer_id": f"C{idx:06d}",
                "full_name": fake.name(),
                "email": fake.unique.email(),
                "segment": rng.choice(["Enterprise", "Mid-Market", "SMB", "Consumer"]),
                "country": rng.choice(["US", "ZA", "GB", "DE", "CA", "AU"]),
                "signup_channel": rng.choice(["paid_search", "organic", "partner", "referral", "direct"]),
                "created_at": created_at.isoformat(),
                "updated_at": (created_at + timedelta(days=rng.randint(0, 120))).isoformat(),
            }
        )

    products = []
    for idx in range(1, product_count + 1):
        products.append(
            {
                "product_id": f"P{idx:04d}",
                "product_name": f"{rng.choice(['Lake', 'Stream', 'Metric', 'Signal'])} {fake.word().title()}",
                "category": rng.choice(["subscription", "data", "analytics", "support"]),
                "unit_price": round(rng.uniform(9, 899), 2),
                "is_recurring": rng.choice([True, True, True, False]),
                "updated_at": (now - timedelta(days=rng.randint(0, 90))).isoformat(),
            }
        )

    transactions = []
    for idx in range(1, transaction_count + 1):
        customer = rng.choice(customers)
        product = rng.choice(products)
        quantity = rng.randint(1, 8)
        discount = rng.choice([0, 0, 0.05, 0.1, 0.15, 0.2])
        occurred_at = now - timedelta(days=rng.randint(0, 540), minutes=rng.randint(0, 1440))
        transactions.append(
            {
                "transaction_id": f"T{idx:08d}",
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": product["unit_price"],
                "discount_pct": discount,
                "currency": "USD",
                "payment_status": rng.choice(["paid", "paid", "paid", "refunded", "failed"]),
                "occurred_at": occurred_at.isoformat(),
                "updated_at": (occurred_at + timedelta(hours=rng.randint(0, 72))).isoformat(),
            }
        )

    support_events = []
    for idx in range(1, support_count + 1):
        customer = rng.choice(customers)
        opened_at = now - timedelta(days=rng.randint(0, 360), minutes=rng.randint(0, 1440))
        severity = rng.choice(["low", "medium", "high", "critical"])
        support_events.append(
            {
                "ticket_id": f"S{idx:07d}",
                "customer_id": customer["customer_id"],
                "severity": severity,
                "channel": rng.choice(["email", "chat", "phone", "portal"]),
                "opened_at": opened_at.isoformat(),
                "resolved_at": (opened_at + timedelta(hours=rng.randint(1, 96))).isoformat(),
                "csat_score": rng.choice([1, 2, 3, 4, 5, None]),
                "updated_at": (opened_at + timedelta(hours=rng.randint(1, 120))).isoformat(),
            }
        )

    web_events = []
    event_types = ["page_view", "trial_started", "demo_requested", "checkout_started", "login"]
    for idx in range(1, event_count + 1):
        customer = rng.choice(customers)
        event_at = now - timedelta(days=rng.randint(0, 180), seconds=rng.randint(0, 86400))
        web_events.append(
            {
                "event_id": f"E{idx:09d}",
                "customer_id": customer["customer_id"],
                "event_type": rng.choice(event_types),
                "utm_source": rng.choice(["google", "linkedin", "newsletter", "partner", "direct"]),
                "device_type": rng.choice(["desktop", "mobile", "tablet"]),
                "event_at": event_at.isoformat(),
                "updated_at": event_at.isoformat(),
            }
        )

    # Inject realistic CDC duplicates and bad records for quality gates to quarantine.
    transactions.extend(transactions[: max(5, scale * 20)])
    transactions.append({**transactions[0], "transaction_id": "", "quantity": -1})
    customers.append({**customers[0], "email": "not-an-email", "updated_at": now.isoformat()})

    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "customers.csv", customers)
    write_csv(output / "products.csv", products)
    write_csv(output / "transactions.csv", transactions)
    write_csv(output / "support_events.csv", support_events)
    with (output / "web_events.jsonl").open("w", encoding="utf-8") as handle:
        for event in web_events:
            handle.write(json.dumps(event) + "\n")

    manifest = {
        "generated_at": now.isoformat(),
        "seed": seed,
        "scale": scale,
        "datasets": DATASETS,
        "note": "Synthetic SaaS revenue, engagement and support data with CDC-style duplicates.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--output", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    generate(args.seed, args.scale, args.output)
