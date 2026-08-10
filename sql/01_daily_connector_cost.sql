-- Portable daily cost model. Source data in this project is entirely synthetic.
SELECT
    usage_date,
    connector,
    owner,
    environment,
    SUM(rows_synced) AS rows_synced,
    ROUND(SUM(connector_cost_usd), 2) AS connector_cost_usd,
    ROUND(SUM(warehouse_cost_usd), 2) AS warehouse_cost_usd,
    ROUND(SUM(total_cost_usd), 2) AS total_cost_usd,
    ROUND(SUM(total_cost_usd) / NULLIF(SUM(rows_synced), 0) * 1000000, 2) AS cost_per_million_rows_usd
FROM raw_connector_costs
GROUP BY usage_date, connector, owner, environment
ORDER BY usage_date, connector;
