# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 3 · SOLUTION — Governed retrieval with AI Search
# MAGIC Chunk → index → filtered retrieval → stale-index fix → semantic search + structured verification.
# MAGIC > Illustrative: package and client names reflect the SDK at the time of writing (`databricks-ai-search`, `AISearchClient`).
# MAGIC > Verify with `pip show databricks-ai-search` and the current AI Search docs before reuse.

# COMMAND ----------

# MAGIC %pip install -q databricks-ai-search

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
dbutils.widgets.text("learner_schema", "")
dbutils.widgets.text("endpoint", "gurpreetsethi-vs-endpoint")
dbutils.widgets.text("embedding_endpoint", "databricks-gte-large-en")
dbutils.widgets.dropdown("chunking", "merged", ["merged", "structure_aware", "fixed_sentence"])
import os, re, sys, time
CAT, SH = dbutils.widgets.get("catalog"), dbutils.widgets.get("shared_schema")
me = spark.sql("select current_user()").first()[0]
LS = dbutils.widgets.get("learner_schema") or "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())
ENDPOINT, EMB, STRATEGY = dbutils.widgets.get("endpoint"), dbutils.widgets.get("embedding_endpoint"), dbutils.widgets.get("chunking")
M = f"{CAT}.{LS}"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {M}")

nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
sys.path.insert(0, f"/Workspace{os.path.dirname(nb)}/../03_ai_search")
import chunking
print("mine:", M, "| endpoint:", ENDPOINT, "| chunking:", STRATEGY)

# COMMAND ----------

# MAGIC %md ## Step 1 · Chunk the authoritative documents (stable ids + filterable metadata)

# COMMAND ----------

docs = [r.asDict() for r in spark.table(f"{CAT}.{SH}.procedure_documents").collect()]
chunks = chunking.chunk_corpus(docs, STRATEGY)
print(len(docs), "documents ->", len(chunks), "chunks ('%s')" % STRATEGY)
SRC = f"{M}.doc_chunks_{STRATEGY}"
spark.createDataFrame(chunks).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(SRC)
spark.sql(f"ALTER TABLE {SRC} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")  # required for Delta Sync
display(spark.table(SRC).select("chunk_id", "heading", "region_code", "status", "effective_date").limit(8))

# COMMAND ----------

# MAGIC %md ## Step 2 · Create a Delta Sync index (TRIGGERED) and wait until it is ready

# COMMAND ----------

from databricks.ai_search.client import AISearchClient
client = AISearchClient()
IDX = f"{M}.doc_chunks_{STRATEGY}_index"
try:
    index = client.get_index(endpoint_name=ENDPOINT, index_name=IDX)
    print("index exists")
except Exception:
    client.create_delta_sync_index(
        endpoint_name=ENDPOINT, index_name=IDX, source_table_name=SRC,
        pipeline_type="TRIGGERED", primary_key="chunk_id",
        embedding_source_column="text", embedding_model_endpoint_name=EMB)
    index = client.get_index(endpoint_name=ENDPOINT, index_name=IDX)
index.wait_until_ready(verbose=False)
print("ready:", IDX)

# COMMAND ----------

# MAGIC %md ## Step 3 · Retrieval: unfiltered vs governed (authority + region)

# COMMAND ----------

COLS = ["chunk_id", "document_id", "title", "region_code", "status", "effective_date", "text"]

def search(query, filters=None, k=4):
    r = index.similarity_search(query_text=query, columns=COLS, filters=filters, num_results=k)
    return [dict(zip(COLS, row[:len(COLS)])) for row in r["result"]["data_array"]]

Q = "What are the steps to lock out and tag a 33kV feeder in Victoria?"
print("UNFILTERED")
for r in search(Q): print(" ", r["chunk_id"], r["status"], r["region_code"], r["effective_date"])
print("GOVERNED (current only, VIC or ALL)")
gov = search(Q, filters={"status": "current", "region_code": ["VIC", "ALL"]})
for r in gov: print(" ", r["chunk_id"], r["status"], r["region_code"], r["effective_date"])

# COMMAND ----------

# MAGIC %md ## Step 4 · Inject only the strongest evidence, with provenance

# COMMAND ----------

def build_evidence(rows, max_chars=3000):
    out, used = [], 0
    for r in rows:
        if used + len(r["text"]) > max_chars: break
        out.append({"source_id": r["chunk_id"], "effective_date": r["effective_date"], "text": r["text"]}); used += len(r["text"])
    return out
ev = build_evidence(gov[:2])
print([e["source_id"] for e in ev], sum(len(e["text"]) for e in ev), "chars")

# COMMAND ----------

# MAGIC %md ## Step 5 · The stale-index scenario (exam favourite)
# MAGIC The source Delta table changes. A TRIGGERED index does not follow until you sync it. **Minimal fix: sync after ingestion.** Do not rebuild, and do not switch to continuous without a latency requirement.

# COMMAND ----------

marker = "ZZ-CLEARANCE-UPDATE"
spark.sql(f"""UPDATE {SRC} SET text = replace(text, '2.0 m in bushfire-prone areas', '2.4 m in bushfire-prone areas ({marker})')
              WHERE document_id = 'PRC-VEG-010'""")
q2 = "minimum clearance for 11kV lines in bushfire-prone areas"
before = " | ".join(r["text"].split("\n")[-1][:90] for r in search(q2, {"status": "current"}, 1))
print("BEFORE sync (index is stale):", marker in before, "|", before)

# COMMAND ----------

index.sync()  # in production: a job task that runs after the ingestion pipeline
for _ in range(40):
    time.sleep(15)
    hit = [r for r in search(q2, {"status": "current"}, 1) if marker in r["text"]]
    if hit: break
print("AFTER sync (fresh):", bool(hit), "after ~%ds" % ((_ + 1) * 15))
assert hit, "index did not pick up the change"

# COMMAND ----------

# MAGIC %md ## Step 6 · Semantic discovery, then structured verification
# MAGIC Fuzzy "similar incidents" is semantic. Exact region/date/status is a structured check on the governed table.

# COMMAND ----------

sem = search("incidents similar to intermittent authentication failures after certificate rotation", {"status": "current"}, 3)
ids = [r["document_id"] for r in sem]
print("semantic candidates:", ids)
display(spark.table(f"{CAT}.{SH}.procedure_documents").where(f"document_id IN ({','.join(repr(i) for i in ids)}) AND region_code = 'NSW' AND status = 'current'")
        .select("document_id", "title", "region_code", "status", "effective_date"))

# COMMAND ----------

# MAGIC %md ## Checks

# COMMAND ----------

def check(n, ok): print(("PASS  " if ok else "FAIL  ") + n); return ok
res = [
  check("governed search returns only current documents", all(r["status"] == "current" for r in gov)),
  check("governed search excludes the superseded VIC procedure", all(r["document_id"] != "PRC-LOTO-001-OLD" for r in gov)),
  check("governed search does not return the NSW variant for a VIC question", all(r["region_code"] in ("VIC", "ALL") for r in gov)),
  check("evidence carries source ids", all(e["source_id"] for e in ev)),
  check("stale index fixed by sync (not rebuild)", bool(hit)),
]
if STRATEGY == "merged":
    res.append(check("steps and witness rule are in ONE chunk", any("witness" in r["text"].lower() and "lock" in r["text"].lower() for r in gov[:1])))
assert all(res), "Lab 3 checks failed"
print("\nLab 3 complete.")
