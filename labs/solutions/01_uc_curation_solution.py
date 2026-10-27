# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1 · Solution — Curate governed context for the GridWorks assistant
# MAGIC Runnable reference. Learners work in `labs/01_uc_curation/01_lab` and compare against this.

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
dbutils.widgets.text("learner_schema", "")
import re, json
CAT = dbutils.widgets.get("catalog")
SH = dbutils.widgets.get("shared_schema")
me = spark.sql("select current_user()").first()[0]
LS = dbutils.widgets.get("learner_schema") or "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CAT}.{LS} COMMENT 'Context engineering lab work for {me}'")
print("shared:", f"{CAT}.{SH}", "| mine:", f"{CAT}.{LS}")

# COMMAND ----------

# MAGIC %md ## Step 1 · Inventory and classify every asset

# COMMAND ----------

display(spark.sql(f"SELECT table_name, comment FROM {CAT}.information_schema.tables WHERE table_schema='{SH}' ORDER BY 1"))

# COMMAND ----------

# authoritative = certified for the agent; derived/draft/raw = must not be in its retrieval space
CLASSIFICATION = {
    "gold_outage_events": "authoritative", "gold_asset_health": "authoritative",
    "gold_work_orders": "authoritative", "gold_crews": "authoritative",
    "gold_crew_availability": "authoritative", "procedure_documents": "authoritative",
    "raw_outage_events": "raw", "raw_inspection_export": "raw_pii",
    "derived_outage_rollup_v1": "derived_stale", "draft_outage_summary_wip": "draft",
    "ce_ground_truth": "internal_test_only",
}

# COMMAND ----------

# MAGIC %md ## Step 2 · Build certified views in YOUR schema and describe them (metadata *is* context)
# MAGIC Learners have read-only access to `ce_shared`, so curation happens in views you own. The view is the agent's boundary.

# COMMAND ----------

T = f"{CAT}.{SH}"
M = f"{CAT}.{LS}"
AUTH = [t for t, c in CLASSIFICATION.items() if c == "authoritative"]
for t in AUTH:
    spark.sql(f"CREATE OR REPLACE VIEW {M}.{t} AS SELECT * FROM {T}.{t}")

DESC = {
 "gold_outage_events": "Certified source for outage events. One row per outage event. Duration = event_end_ts - event_start_ts. region_code is one of VIC, NSW, QLD, SA. priority_code: P1 critical, P2 urgent (priority two), P3 routine. is_planned=true marks planned outages, which are reported separately for SAIDI.",
 "gold_asset_health": "Certified asset-health scores, one current row per asset. health_band: poor (<50), fair (50-74), good (75+). is_critical_feeder marks a feeder supplying a hospital, water treatment plant or more than 5,000 customers. last_inspection_date is the most recent completed inspection.",
 "gold_work_orders": "Certified maintenance work orders. status: open, in_progress, complete, cancelled. amount_aud is in Australian dollars.",
 "gold_crews": "Certified crew roster with region and skill. HV switching requires skill HV_switching.",
 "gold_crew_availability": "Certified 14-day crew availability. available=true means the crew can be dispatched on work_date.",
 "procedure_documents": "Procedure and standard documents. Use only status=current for guidance; superseded and draft versions must not be used.",
}
for t, d in DESC.items():
    spark.sql(f"COMMENT ON TABLE {M}.{t} IS '{d}'")
spark.sql(f"COMMENT ON COLUMN {M}.gold_outage_events.priority_code IS 'Operational priority: P1 = public safety or critical infrastructure, P2 = more than 500 customers or critical feeder (priority two), P3 = other.'")
spark.sql(f"COMMENT ON COLUMN {M}.gold_outage_events.customers_interrupted IS 'Customers who lost supply. Used with outage minutes to compute SAIDI.'")

# COMMAND ----------

# MAGIC %md ## Step 3 · Tag authority on your views (so governance can act on it)

# COMMAND ----------

for t in AUTH:
    spark.sql(f"ALTER VIEW {M}.{t} SET TAGS ('ce_certification' = 'certified', 'ce_asset_class' = 'authoritative')")

# COMMAND ----------

# MAGIC %md ## Step 4 · A curated view where raw access is too broad

# COMMAND ----------

V = f"{M}.curated_asset_health_for_assistant"
spark.sql(f"""
CREATE OR REPLACE VIEW {V}
COMMENT 'Assistant-safe, current asset-health view. Excludes technician and customer PII.'
AS SELECT asset_id, asset_class, region_code, is_critical_feeder, health_score, health_band,
          last_inspection_date, next_inspection_due_date
   FROM {M}.gold_asset_health WHERE is_current = true""")
display(spark.sql(f"SELECT * FROM {V} LIMIT 5"))

# COMMAND ----------

# MAGIC %md ## Step 5 · Write the context contract

# COMMAND ----------

contract = {
    "agent": "gridworks-operations-assistant",
    "purpose": "Answer outage, asset-health, work-order and procedure questions for control-room staff",
    "allowed_sources": [
        {"name": f"{M}.gold_outage_events", "authority": "certified", "freshness": "daily", "use": "structured"},
        {"name": V, "authority": "certified", "freshness": "daily", "use": "structured"},
        {"name": f"{M}.gold_work_orders", "authority": "certified", "freshness": "daily", "use": "structured"},
        {"name": f"{M}.gold_crew_availability", "authority": "certified", "freshness": "daily", "use": "structured"},
        {"name": f"{M}.procedure_documents", "authority": "certified", "freshness": "on_change", "use": "retrieval", "filter": "status = 'current'"},
    ],
    "forbidden_sources": ["raw_*", "draft_*", "derived_*", "raw_inspection_export"],
    "pii_policy": "No technician or customer identifiers in agent context",
    "on_conflict": "certified source wins; cite source id",
}
spark.createDataFrame([(json.dumps(contract),)], ["contract_json"]).write.mode("overwrite").saveAsTable(f"{CAT}.{LS}.context_contract")
print(json.dumps(contract, indent=2)[:600])

# COMMAND ----------

# MAGIC %md ## Checks

# COMMAND ----------

def check(name, ok):
    print(("PASS  " if ok else "FAIL  ") + name); return ok

res = []
tags = {(r.table_name, r.tag_name): r.tag_value for r in spark.sql(
    f"SELECT table_name, tag_name, tag_value FROM {CAT}.information_schema.table_tags WHERE schema_name='{LS}'").collect()}
for t in AUTH:
    cmt = spark.sql(f"SELECT comment FROM {CAT}.information_schema.tables WHERE table_schema='{LS}' AND table_name='{t}'").first()[0]
    res.append(check(f"{t} has a description of 40+ chars", bool(cmt) and len(cmt) >= 40))
    res.append(check(f"{t} tagged certified", tags.get((t, "ce_certification")) == "certified"))
res.append(check("you classified all 11 shared tables", len(CLASSIFICATION) == 11))
cols = [c.name for c in spark.table(V).schema]
res.append(check("curated view has no PII columns", not {"technician_name", "technician_mobile", "customer_contact_email"} & set(cols)))
res.append(check("contract forbids raw/draft/derived", all(x in contract["forbidden_sources"] for x in ("raw_*", "draft_*", "derived_*"))))
res.append(check("contract lists no non-certified source", all(not any(p in s["name"] for p in ("raw_", "draft_", "derived_")) for s in contract["allowed_sources"])))
assert all(res), "Lab 1 checks failed"
print("\nLab 1 complete.")
