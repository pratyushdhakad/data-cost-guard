from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from .analytics import detect_anomalies, summarize, validate_input
from .generate_data import generate_synthetic_data
from .report import build_dashboard, write_summary


def run(project_root: Path) -> dict[str, object]:
    data_path = project_root / "data" / "connector_costs.csv"
    generate_synthetic_data(data_path)
    raw = pd.read_csv(data_path)
    validate_input(raw)

    with sqlite3.connect(":memory:") as connection:
        raw.to_sql("raw_connector_costs", connection, index=False, if_exists="replace")
        sql = (project_root / "sql" / "01_daily_connector_cost.sql").read_text(encoding="utf-8")
        daily = pd.read_sql_query(sql, connection)

    scored = detect_anomalies(daily)
    result = summarize(daily, scored)
    artifacts = project_root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    daily.to_csv(artifacts / "daily_connector_cost.csv", index=False)
    scored[scored["is_anomaly"]].to_csv(artifacts / "anomalies.csv", index=False)
    write_summary(result, artifacts / "summary.json")
    build_dashboard(daily, scored, result, project_root / "dashboard" / "index.html")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Data Cost Guard pipeline")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    summary = run(args.project_root.resolve())
    print(f"Pipeline complete: {summary}")


if __name__ == "__main__":
    main()
