# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Load the ANZ GridWorks dataset
# MAGIC Facilitator/admin notebook. Run once per cohort. Creates the shared, read-only schema every lab reads from.
# MAGIC
# MAGIC The data is **deliberately messy** (raw, derived, draft and certified assets coexist) so Lab 1 has something to curate.
# MAGIC All data is fictional.

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("schema", "ce_shared")
CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")

# COMMAND ----------

import sys, os

# The generator lives next to this notebook's parent folder (data/ in the bundle, or uploaded beside it).
nb_dir = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
for cand in (f"/Workspace{nb_dir}/../../data", f"/Workspace{nb_dir}"):
    if os.path.exists(os.path.join(cand, "gridworks_gen.py")):
        sys.path.insert(0, cand)
        break
import gridworks_gen as gen

tables = gen.generate()
print({k: len(v) for k, v in tables.items()})

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA} COMMENT 'Context Engineering enablement: shared GridWorks data (fictional)'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.docs COMMENT 'GridWorks procedure documents (markdown)'")

# COMMAND ----------

from pyspark.sql import Row

for name, rows in tables.items():
    if not rows:
        continue
    df = spark.createDataFrame([Row(**r) for r in rows])
    (df.write.mode("overwrite").option("overwriteSchema", "true")
       .saveAsTable(f"{CATALOG}.{SCHEMA}.{name}"))
    print("wrote", name, df.count())

# COMMAND ----------

# Documents as files too, so Lab 3 can practise parsing + chunking from a volume.
vol = f"/Volumes/{CATALOG}/{SCHEMA}/docs"
for d in tables["procedure_documents"]:
    with open(f"{vol}/{d['document_id']}.md", "w") as f:
        f.write(f"---\ndocument_id: {d['document_id']}\nregion_code: {d['region_code']}\n"
                f"status: {d['status']}\neffective_date: {d['effective_date']}\n---\n{d['text']}\n")
print(len(os.listdir(vol)), "documents in", vol)

# COMMAND ----------

# Ground truth for Lab 2 and Lab 6 gold sets. Computed from the data, so it cannot drift.
truth = gen.expected_answers(tables)
spark.createDataFrame([Row(key=k, value=str(v)) for k, v in truth.items()]) \
     .write.mode("overwrite").saveAsTable(f"{CATALOG}.{SCHEMA}.ce_ground_truth")
display(spark.table(f"{CATALOG}.{SCHEMA}.ce_ground_truth"))

# COMMAND ----------

# MAGIC %md
# MAGIC **Sanity checks the facilitator should see pass:**
# MAGIC - `raw_outage_events` has more rows than `gold_outage_events` (duplicates) and mixed region spellings
# MAGIC - `derived_outage_rollup_v1` exists and is stale (built March 2026, wrong SAIDI formula)
# MAGIC - `raw_inspection_export` contains technician names/mobiles (PII), the reason a curated view must exist

# COMMAND ----------

assert spark.table(f"{CATALOG}.{SCHEMA}.raw_outage_events").count() > spark.table(f"{CATALOG}.{SCHEMA}.gold_outage_events").count()
assert spark.table(f"{CATALOG}.{SCHEMA}.raw_outage_events").select("region_code").distinct().count() > 4
print("OK")
