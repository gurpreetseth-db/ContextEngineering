-- Freshness/provenance for the KPI panel.
SELECT CAST(MAX(event_start_ts) AS STRING) AS data_through,
       COUNT(*) AS outage_rows
FROM gsethi.ce_shared.gold_outage_events
