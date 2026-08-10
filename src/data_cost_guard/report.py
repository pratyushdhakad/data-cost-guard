from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _line_chart(daily: pd.DataFrame, width: int = 900, height: int = 250) -> str:
    values = daily["total_cost_usd"].to_numpy()
    low, high = float(values.min()), float(values.max())
    span = max(high - low, 1)
    points = []
    for index, value in enumerate(values):
        x = 20 + index * (width - 40) / max(len(values) - 1, 1)
        y = 15 + (high - value) * (height - 35) / span
        points.append(f"{x:.1f},{y:.1f}")
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-label="Daily platform cost trend">
      <line x1="20" y1="{height-20}" x2="{width-20}" y2="{height-20}" stroke="#dbe2ea"/>
      <polyline fill="none" stroke="#2563eb" stroke-width="4" points="{' '.join(points)}"/>
      <text x="20" y="14" fill="#64748b" font-size="13">High {_money(high)}</text>
      <text x="20" y="{height-3}" fill="#64748b" font-size="13">Low {_money(low)}</text>
    </svg>'''


def build_dashboard(frame: pd.DataFrame, scored: pd.DataFrame, summary: dict[str, object], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    daily = frame.groupby("usage_date", as_index=False)["total_cost_usd"].sum().tail(90)
    anomalies = scored[scored["is_anomaly"]].sort_values("excess_cost_usd", ascending=False).head(8)
    rows = "".join(
        f"<tr><td>{html.escape(str(r.usage_date))}</td><td>{html.escape(str(r.connector))}</td>"
        f"<td>{_money(r.total_cost_usd)}</td><td>{r.anomaly_score:.1f}</td><td>{_money(r.excess_cost_usd)}</td></tr>"
        for r in anomalies.itertuples()
    )
    cards = [
        ("30-day cost", _money(float(summary["last_30_day_cost_usd"]))),
        ("30-day forecast", _money(float(summary["next_30_day_forecast_usd"]))),
        ("Cost anomalies", str(summary["anomaly_count"])),
        ("Excess cost found", _money(float(summary["identified_excess_cost_usd"]))),
    ]
    card_html = "".join(f'<section class="card"><span>{label}</span><strong>{value}</strong></section>' for label, value in cards)
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Data Cost Guard</title><style>
:root{{--ink:#10233f;--muted:#64748b;--line:#dbe2ea;--blue:#2563eb;--bg:#f5f7fb}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px Inter,system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:48px 24px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:end}}h1{{margin:0;font-size:38px}}p{{color:var(--muted)}}.badge{{background:#dbeafe;color:#1d4ed8;padding:8px 12px;border-radius:999px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:28px 0}}.card,.panel{{background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 8px 24px #10233f0c}}.card{{padding:20px}}.card span{{display:block;color:var(--muted);font-size:13px}}.card strong{{display:block;font-size:27px;margin-top:8px}}.panel{{padding:24px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;text-align:left;border-bottom:1px solid var(--line)}}th{{color:var(--muted);font-size:12px;text-transform:uppercase}}footer{{color:var(--muted);margin-top:24px}}@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,1fr)}}header{{display:block}}}}
</style></head><body><main><header><div><h1>Data Cost Guard</h1><p>Connector and warehouse cost intelligence · synthetic demonstration data</p></div><div class="badge">Updated {summary['latest_date']}</div></header>
<div class="grid">{card_html}</div><section class="panel"><h2>90-day platform cost trend</h2>{_line_chart(daily)}</section>
<section class="panel"><h2>Priority anomalies</h2><table><thead><tr><th>Date</th><th>Connector</th><th>Cost</th><th>Score</th><th>Excess</th></tr></thead><tbody>{rows}</tbody></table></section>
<footer>Portfolio demonstration. All data is synthetic; metrics do not represent any employer.</footer></main></body></html>'''
    output.write_text(document, encoding="utf-8")
    return output


def write_summary(summary: dict[str, object], output: Path) -> None:
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
