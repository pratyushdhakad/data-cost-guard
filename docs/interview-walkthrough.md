# Five-minute interview walkthrough

## 1. Business problem

Data-platform spend often grows across connectors, warehouses, and teams without one decision-ready view. Data Cost Guard allocates cost, identifies abnormal usage, and turns the result into a prioritized review queue.

## 2. Technical approach

The project creates deterministic synthetic billing data, validates its schema, models daily cost in SQL, applies robust rolling anomaly detection in Python, forecasts the next 30 days, and generates a static executive dashboard.

## 3. Why robust anomaly detection

A mean and standard deviation can be distorted by the spike being investigated. A rolling median and median absolute deviation provide a more stable baseline for operational cost data.

## 4. Quality and reproducibility

Unit tests cover schema validation, known anomaly recovery, forecasting, and end-to-end artifact generation. GitHub Actions runs the same checks on every change.

## 5. Trade-offs and next step

The forecast is intentionally interpretable, not a complex time-series model. In production I would compare it against seasonal baselines, add budget thresholds, and route alerts to accountable owners with feedback labels.
