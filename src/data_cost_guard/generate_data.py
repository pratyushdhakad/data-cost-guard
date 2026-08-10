from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np


CONNECTORS = {
    "shopify_orders": ("commerce", 82.0, 1_800_000),
    "meta_ads": ("marketing", 63.0, 920_000),
    "google_ads": ("marketing", 58.0, 780_000),
    "zendesk_tickets": ("support", 41.0, 310_000),
    "netsuite_finance": ("finance", 74.0, 540_000),
    "warehouse_inventory": ("operations", 69.0, 1_100_000),
    "subscription_events": ("growth", 91.0, 2_200_000),
    "product_analytics": ("product", 77.0, 1_500_000),
}


def generate_synthetic_data(
    output_path: Path,
    *,
    seed: int = 42,
    start: date = date(2026, 2, 1),
    days: int = 181,
) -> Path:
    """Create stable synthetic connector billing data with known anomalies."""
    rng = np.random.default_rng(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    anomaly_days = {
        ("shopify_orders", 143): 2.8,
        ("meta_ads", 151): 2.3,
        ("subscription_events", 160): 3.1,
        ("product_analytics", 167): 2.5,
    }

    for day_index in range(days):
        current = start + timedelta(days=day_index)
        weekday_factor = 0.82 if current.weekday() >= 5 else 1.0
        trend_factor = 1 + day_index * 0.0012
        for connector, (owner, base_cost, base_rows) in CONNECTORS.items():
            noise = max(0.72, rng.normal(1.0, 0.075))
            anomaly_factor = anomaly_days.get((connector, day_index), 1.0)
            rows_synced = int(base_rows * weekday_factor * trend_factor * noise * anomaly_factor)
            connector_cost = base_cost * weekday_factor * trend_factor * noise * anomaly_factor
            warehouse_cost = 0.000014 * rows_synced + rng.uniform(5.0, 12.0)
            rows.append(
                {
                    "usage_date": current.isoformat(),
                    "connector": connector,
                    "owner": owner,
                    "environment": "production",
                    "rows_synced": rows_synced,
                    "connector_cost_usd": round(connector_cost, 2),
                    "warehouse_cost_usd": round(warehouse_cost, 2),
                    "total_cost_usd": round(connector_cost + warehouse_cost, 2),
                }
            )

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output_path
