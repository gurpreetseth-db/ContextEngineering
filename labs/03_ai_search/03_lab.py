# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 3 · Governed retrieval with AI Search
# MAGIC **Time:** 55 min core · **Maps to exam:** Domain 3 (RAG pipeline, chunking, AI Search diagnosis), Domain 4 (semantic vs structured retrieval)
# MAGIC
# MAGIC **Scenario.** Control-room staff ask about isolation procedures. The corpus holds current, superseded and draft versions, plus regional variants.
# MAGIC Retrieval must return the *authoritative, permitted, fresh* chunk, and the answer must carry source ids.
# MAGIC
# MAGIC **Tiers:** *Core* = every `TODO`. *Skip-ahead* = run `labs/solutions/03_ai_search_solution`. *Stretch* = compare chunking strategies (Step 7).
# MAGIC > Illustrative: package/client names reflect the SDK at the time of writing. Verify with `pip show databricks-ai-search`.

# COMMAND ----------

# MAGIC %pip install -q databricks-ai-search

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
dbutils.widgets.text("endpoint", "gurpreetsethi-vs-endpoint")   # facilitator provides
dbutils.widgets.text("embedding_endpoint", "databricks-gte-large-en")
dbutils.widgets.dropdown("chunking", "merged", ["merged", "structure_aware", "fixed_sentence"])
import os, re, sys, time
CAT, SH = dbutils.widgets.get("catalog"), dbutils.widgets.get("shared_schema")
me = spark.sql("select current_user()").first()[0]
LS = "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())
ENDPOINT, EMB, STRATEGY = dbutils.widgets.get("endpoint"), dbutils.widgets.get("embedding_endpoint"), dbutils.widgets.get("chunking")
M = f"{CAT}.{LS}"
nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
sys.path.insert(0, f"/Workspace{os.path.dirname(nb)}")
import chunking

# COMMAND ----------

# MAGIC %md ## Step 1 · Chunk the authoritative documents
# MAGIC Three strategies are provided. Start with `merged`. In Step 7 you will see why.

# COMMAND ----------

docs = [r.asDict() for r in spark.table(f"{CAT}.{SH}.procedure_documents").collect()]
chunks = chunking.chunk_corpus(docs, STRATEGY)
print(len(docs), "documents ->", len(chunks), "chunks")
SRC = f"{M}.doc_chunks_{STRATEGY}"
spark.createDataFrame(chunks).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(SRC)
spark.sql(f"ALTER TABLE {SRC} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
display(spark.table(SRC).select("chunk_id", "heading", "region_code", "status").limit(8))

# COMMAND ----------

# MAGIC %md ## Step 2 · Create the Delta Sync index (TRIGGERED)

# COMMAND ----------

from databricks.ai_search.client import AISearchClient
client = AISearchClient()
IDX = f"{M}.doc_chunks_{STRATEGY}_index"
# TODO: create_delta_sync_index(endpoint_name, index_name, source_table_name, pipeline_type="TRIGGERED",
#       primary_key="chunk_id", embedding_source_column="text", embedding_model_endpoint_name=EMB)
#       then get_index(...) and index.wait_until_ready()
index = None

# COMMAND ----------

# MAGIC %md ## Step 3 · Retrieval: see the problem, then govern it

# COMMAND ----------

COLS = ["chunk_id", "document_id", "title", "region_code", "status", "effective_date", "text"]
def search(query, filters=None, k=4):
    r = index.similarity_search(query_text=query, columns=COLS, filters=filters, num_results=k)
    return [dict(zip(COLS, row[:len(COLS)])) for row in r["result"]["data_array"]]

Q = "What are the steps to lock out and tag a 33kV feeder in Victoria?"
for r in search(Q): print(r["chunk_id"], r["status"], r["region_code"])      # which of these must NOT reach the agent?

# COMMAND ----------

# TODO: add `filters` so only authoritative, permitted chunks are returned (current status; Victoria or all-region).
#       Filter syntax: {"column": value} and {"column": [v1, v2]} for IN.
gov = search(Q)  # <- change this call

# COMMAND ----------

# MAGIC %md ## Step 4 · Inject only the strongest evidence, with provenance
# MAGIC Return at most N characters, each item carrying `source_id` and `effective_date`.

# COMMAND ----------

def build_evidence(rows, max_chars=3000):
    # TODO: stop when the budget is exceeded; return [{"source_id","effective_date","text"}]
    return []
ev = build_evidence(gov[:2])

# COMMAND ----------

# MAGIC %md ## Step 5 · Stale index: diagnose and apply the *minimal* fix
# MAGIC The source table changes (a clearance distance is amended). The index is TRIGGERED. Run the next cell to see the symptom.

# COMMAND ----------

marker = "ZZ-CLEARANCE-UPDATE"
spark.sql(f"""UPDATE {SRC} SET text = replace(text, '2.0 m in bushfire-prone areas', '2.4 m in bushfire-prone areas ({marker})')
              WHERE document_id = 'PRC-VEG-010'""")
q2 = "minimum clearance for 11kV lines in bushfire-prone areas"
print("stale? ->", marker not in " ".join(r["text"] for r in search(q2, {"status": "current"}, 1)))

# COMMAND ----------

# MAGIC %md
# MAGIC Pick the **smallest governed fix**: (a) drop and recreate the index, (b) switch to CONTINUOUS, (c) move to Direct Access, (d) sync after the ingestion step.
# MAGIC Write down *why the other three are wrong for a nightly-refresh requirement* before you apply yours.

# COMMAND ----------

# TODO: apply your fix, then wait until a search for q2 returns the marker.
hit = []

# COMMAND ----------

# MAGIC %md ## Step 6 · Semantic discovery, then structured verification
# MAGIC "Incidents *similar to* intermittent authentication failures after certificate rotation" is fuzzy → semantic.
# MAGIC "In NSW, current" is exact → structured. Combine them.

# COMMAND ----------

# TODO: semantic search (top 3), then a structured query on procedure_documents that verifies region = 'NSW' and status = 'current'.

# COMMAND ----------

# MAGIC %md ## Step 7 · Stretch: chunking matters
# MAGIC Re-run Steps 1 to 3 with `chunking = fixed_sentence`, then `structure_aware`. For the isolation question, does a single chunk contain **both** the steps and the witness rule?
# MAGIC Which strategy would you choose for broad synthesis questions, and which for narrow lookups?

# COMMAND ----------

# MAGIC %md ## Checks

# COMMAND ----------

def check(n, ok): print(("PASS  " if ok else "FAIL  ") + n); return ok
res = [
  check("index created", index is not None),
  check("governed search returns only current documents", bool(gov) and all(r["status"] == "current" for r in gov)),
  check("superseded VIC procedure excluded", bool(gov) and all(r["document_id"] != "PRC-LOTO-001-OLD" for r in gov)),
  check("NSW variant excluded for a VIC question", bool(gov) and all(r["region_code"] in ("VIC", "ALL") for r in gov)),
  check("evidence carries source ids", bool(ev) and all(e["source_id"] for e in ev)),
  check("stale index fixed", bool(hit)),
]
print("\nLab 3 complete." if all(res) else "\nKeep going: fix the FAIL lines.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debrief
# MAGIC - Which single change (metadata filter) removed the most harm? Would a larger model have fixed it?
# MAGIC - **Exam link (Domain 3):** a TRIGGERED Delta Sync index serving yesterday's data after a nightly refresh → *sync after ingestion*, not rebuild, not continuous.
# MAGIC - **Exam link (Domain 3):** weakly structured, mixed-length text → recursive splitting around 512 to 1,024 tokens with 10 to 15% overlap *for that scenario*. Not a universal constant.
