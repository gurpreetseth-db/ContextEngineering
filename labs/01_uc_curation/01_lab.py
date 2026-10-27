# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1 · Curate governed context for the GridWorks assistant
# MAGIC **Time:** 50 min core · **Maps to exam:** Domain 3 (retrieval + governance), Domain 1 (product selection)
# MAGIC
# MAGIC **Scenario.** The GridWorks assistant will be pointed at `ce_shared`. It contains certified, raw, derived and draft assets side by side.
# MAGIC Your job: decide what the agent may see, make that obvious in metadata, and write it down as a *context contract*.
# MAGIC
# MAGIC > Governance is part of context construction, not a final checklist. Metadata, certification and permissions decide what the agent retrieves and trusts.
# MAGIC
# MAGIC **Tiers:** *Core* = do every `TODO`. *Skip-ahead* = run `labs/solutions/01_uc_curation_solution`. *Stretch* = Step 6.

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
import re, json
CAT = dbutils.widgets.get("catalog"); SH = dbutils.widgets.get("shared_schema")
me = spark.sql("select current_user()").first()[0]
LS = "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CAT}.{LS}")
T = f"{CAT}.{SH}"
print("shared:", T, "| yours:", f"{CAT}.{LS}")

# COMMAND ----------

# MAGIC %md ## Step 1 · Inventory
# MAGIC Look at every asset. Ask the five questions for each: **Need, Timing, Authority, Efficiency, Proof**.

# COMMAND ----------

display(spark.sql(f"SELECT table_name, comment FROM {CAT}.information_schema.tables WHERE table_schema='{SH}' ORDER BY 1"))

# COMMAND ----------

# MAGIC %md
# MAGIC Peek at three suspicious tables, then classify. Questions to answer in your notes:
# MAGIC 1. Which two tables disagree about SAIDI, and why?
# MAGIC 2. Which table would leak personal data into the prompt?
# MAGIC 3. Why is `gold_outage_events` safer than `raw_outage_events` for "How many P2 outages in Victoria?"

# COMMAND ----------

display(spark.sql(f"SELECT region_code, priority_code, count(*) n FROM {T}.raw_outage_events GROUP BY 1,2 ORDER BY 1,2"))
display(spark.sql(f"SELECT * FROM {T}.derived_outage_rollup_v1 LIMIT 5"))
display(spark.sql(f"SELECT * FROM {T}.raw_inspection_export LIMIT 3"))

# COMMAND ----------

# TODO: classify every table as one of: authoritative | raw | raw_pii | derived_stale | draft | internal_test_only
CLASSIFICATION = {
    "gold_outage_events": "???",
    # ... add all 11 tables
}

# COMMAND ----------

# MAGIC %md ## Step 2 · Build certified views in YOUR schema and describe them
# MAGIC You have read-only access to `ce_shared`, so you curate through **views you own**. The view is the agent's boundary.
# MAGIC Write descriptions an agent (and a new analyst) can act on: grain, allowed values, definitions, caveats.
# MAGIC *Hint:* a good description answers "what is one row?", "what do the codes mean?", and "what should I not use this for?"

# COMMAND ----------

M = f"{CAT}.{LS}"
AUTH = [t for t, c in CLASSIFICATION.items() if c == "authoritative"]
# TODO: for each authoritative table, CREATE OR REPLACE VIEW {M}.<name> AS SELECT * FROM {T}.<name>

# TODO: COMMENT ON TABLE {M}.<name> IS '...'   (works for views)  for the 6 authoritative objects
#       COMMENT ON COLUMN {M}.gold_outage_events.priority_code IS '...'   and customers_interrupted
#       (there is no ALTER VIEW ... ALTER COLUMN ... COMMENT)

# COMMAND ----------

# MAGIC %md ## Step 3 · Tag authority on your views
# MAGIC Tags let governance (and retrieval filters) act on your decision.

# COMMAND ----------

# TODO: ALTER VIEW {M}.<name> SET TAGS ('ce_certification' = 'certified', 'ce_asset_class' = 'authoritative')

# COMMAND ----------

# MAGIC %md ## Step 4 · A curated view where raw access is too broad
# MAGIC The assistant needs asset health but never technician or customer details.

# COMMAND ----------

V = f"{M}.curated_asset_health_for_assistant"
# TODO: CREATE OR REPLACE VIEW {V} ... from {M}.gold_asset_health, current rows only, with a COMMENT, no PII columns.

# COMMAND ----------

# MAGIC %md ## Step 5 · Write the context contract
# MAGIC One dict, five fields: purpose, allowed sources (with authority, freshness, use), forbidden sources, PII policy, conflict rule.

# COMMAND ----------

contract = {
    "agent": "gridworks-operations-assistant",
    "purpose": "<TODO>",
    "allowed_sources": [],       # TODO: name, authority, freshness, use (structured|retrieval), optional filter
    "forbidden_sources": [],     # TODO
    "pii_policy": "<TODO>",
    "on_conflict": "<TODO>",
}
spark.createDataFrame([(json.dumps(contract),)], ["contract_json"]).write.mode("overwrite").saveAsTable(f"{CAT}.{LS}.context_contract")

# COMMAND ----------

# MAGIC %md ## Step 6 · Stretch
# MAGIC Pair up. One person is the **context engineer**, the other is the **risk reviewer**. The reviewer tries to find one way the agent could still
# MAGIC see PII or a stale source. Decide the smallest governed fix. (Hint: what does `SHOW GRANTS ON TABLE` say about who can read `raw_inspection_export`?)

# COMMAND ----------

# MAGIC %md ## Checks
# MAGIC Re-run until everything passes.

# COMMAND ----------

def check(name, ok):
    print(("PASS  " if ok else "FAIL  ") + name); return ok

res = []
tags = {(r.table_name, r.tag_name): r.tag_value for r in spark.sql(
    f"SELECT table_name, tag_name, tag_value FROM {CAT}.information_schema.table_tags WHERE schema_name='{LS}'").collect()}
res.append(check("you classified all 11 shared tables", len(CLASSIFICATION) == 11))
for t in AUTH:
    try:
        cmt = spark.sql(f"SELECT comment FROM {CAT}.information_schema.tables WHERE table_schema='{LS}' AND table_name='{t}'").first()[0]
    except Exception:
        cmt = None
    res.append(check(f"{t} view has a description of 40+ chars", bool(cmt) and len(cmt) >= 40))
    res.append(check(f"{t} view tagged certified", tags.get((t, "ce_certification")) == "certified"))
try:
    cols = {c.name for c in spark.table(V).schema}
    res.append(check("curated view has no PII columns", not {"technician_name", "technician_mobile", "customer_contact_email"} & cols))
except Exception:
    res.append(check("curated view exists", False))
res.append(check("contract has forbidden sources", len(contract["forbidden_sources"]) >= 3))
res.append(check("contract allows only certified tables", all(not any(p in s["name"] for p in ("raw_", "draft_", "derived_")) for s in contract["allowed_sources"]) and len(contract["allowed_sources"]) >= 4))
print("\nLab 1 complete." if all(res) else "\nKeep going: fix the FAIL lines.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debrief
# MAGIC - Which single metadata change made the biggest difference to what an agent could *safely* retrieve?
# MAGIC - Where would a larger model have helped here? (Expected answer: nowhere.)
# MAGIC - **Exam link (Domain 3):** *design a governance strategy that constrains the agent's retrieval space to authoritative sources before deployment.*
