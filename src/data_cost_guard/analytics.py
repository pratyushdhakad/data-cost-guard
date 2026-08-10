from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "usage_date",
    "connector",
    "owner",
    "rows_synced",
    "connector_cost_usd",
    "warehouse_cost_usd",
    "total_cost_usd",
}


def validate_input(frame: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError("Input data is empty")
    if (frame["total_cost_usd"] < 0).any():
        raise ValueError("Costs must be non-negative")


def detect_anomalies(frame: pd.DataFrame, window: int = 28, threshold: float = 4.0) -> pd.DataFrame:
    """Flag unusual daily connector cost using a rolling robust z-score."""
    validate_input(frame)
    data = frame.copy().sort_values(["connector", "usage_date"])

    def score(group: pd.DataFrame) -> pd.DataFrame:
        connector = group.name
        prior = group["total_cost_usd"].shift(1)
        median = prior.rolling(window, min_periods=14).median()
        deviation = (prior - median).abs()
        mad = deviation.rolling(window, min_periods=14).median()
        robust_z = 0.6745 * (group["total_cost_usd"] - median) / mad.replace(0, np.nan)
        group = group.copy()
        group["connector"] = connector
        group["baseline_cost_usd"] = median.round(2)
        group["anomaly_score"] = robust_z.replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
        group["is_anomaly"] = group["anomaly_score"] >= threshold
        group["excess_cost_usd"] = (group["total_cost_usd"] - median).clip(lower=0).fillna(0).round(2)
        return group

    return data.groupby("connector", group_keys=False).apply(score, include_groups=False).reset_index(drop=True)


def forecast_month_end(frame: pd.DataFrame, horizon_days: int = 30) -> dict[str, float]:
    daily = frame.groupby("usage_date", as_index=False)["total_cost_usd"].sum().sort_values("usage_date")
    lookback = daily.tail(30)
    x = np.arange(len(lookback), dtype=float)
    slope, intercept = np.polyfit(x, lookback["total_cost_usd"].to_numpy(), 1)
    future_x = np.arange(len(lookback), len(lookback) + horizon_days, dtype=float)
    projected = np.maximum(0, slope * future_x + intercept)
    return {
        "current_daily_run_rate_usd": round(float(lookback["total_cost_usd"].mean()), 2),
        "next_30_day_forecast_usd": round(float(projected.sum()), 2),
        "daily_trend_usd": round(float(slope), 2),
    }


def summarize(frame: pd.DataFrame, scored: pd.DataFrame) -> dict[str, object]:
    latest_date = pd.to_datetime(frame["usage_date"]).max()
    recent_start = latest_date - pd.Timedelta(days=29)
    recent = frame[pd.to_datetime(frame["usage_date"]) >= recent_start]
    anomalies = scored[scored["is_anomaly"]]
    owner_cost = recent.groupby("owner")["total_cost_usd"].sum().sort_values(ascending=False)
    forecast = forecast_month_end(frame)
    return {
        "latest_date": latest_date.date().isoformat(),
        "last_30_day_cost_usd": round(float(recent["total_cost_usd"].sum()), 2),
        "anomaly_count": int(len(anomalies)),
        "identified_excess_cost_usd": round(float(anomalies["excess_cost_usd"].sum()), 2),
        "highest_cost_owner": str(owner_cost.index[0]),
        **forecast,
    }
