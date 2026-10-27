-- Critical feeders in the poor health band: candidates for a reinspection request.
SELECT asset_id,
       region_code,
       health_score,
       CAST(last_inspection_date AS STRING) AS last_inspection_date,
       CAST(next_inspection_due_date AS STRING) AS next_inspection_due_date
FROM gsethi.ce_shared.gold_asset_health
WHERE is_critical_feeder = true AND health_band = 'poor'
ORDER BY health_score ASC
LIMIT 10
