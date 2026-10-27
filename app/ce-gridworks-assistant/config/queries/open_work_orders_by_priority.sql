-- Open = status open OR in_progress (certified definition; see Lab 2). Certified source only.
SELECT priority_code, COUNT(*) AS open_count
FROM gsethi.ce_shared.gold_work_orders
WHERE status IN ('open', 'in_progress')
GROUP BY priority_code
ORDER BY priority_code
