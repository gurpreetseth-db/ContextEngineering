-- Unplanned outages only (planned outages are reported separately for SAIDI).
SELECT region_code, COUNT(*) AS outages
FROM gsethi.ce_shared.gold_outage_events
WHERE is_planned = false
GROUP BY region_code
ORDER BY outages DESC
