# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 2 · SOLUTION — Tune a Genie space
# MAGIC **Time:** 45 min core · **Maps to exam:** Domain 2 (Genie instructions/sample questions/trusted SQL) and Domain 3 (Genie configuration)
# MAGIC
# MAGIC You start with a Genie space that has the right tables and nothing else. A 6-question test set exposes where it fails.
# MAGIC Fix the failures with the **smallest, correct control**. Do not add tables and do not change the model.
# MAGIC
# MAGIC | Genie control | Use it for |
# MAGIC |---|---|
# MAGIC | General instructions | Business vocabulary, definitions, defaults, interpretation rules |
# MAGIC | Sample questions | Representative user phrasing and discoverability |
# MAGIC | Trusted SQL (example SQL) | Validated query patterns for important recurring questions |
# MAGIC | SQL expressions (filters, measures) | Reusable calculation and filter logic |
# MAGIC
# MAGIC > Illustrative API usage. Genie API paths, fields and serialization can change: check the current Genie API docs and your installed `databricks-sdk` version before reusing.

# COMMAND ----------

dbutils.widgets.text("warehouse_id", "")
import os, sys, re
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
me = w.current_user.me().user_name

nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
sys.path.insert(0, f"/Workspace{os.path.dirname(nb)}/../02_genie")
import genie_harness as h

def api(method, path, body=None):
    return w.api_client.do(method, path, body=body) or {}

WH = dbutils.widgets.get("warehouse_id") or next(x.id for x in w.warehouses.list())
PARENT = f"/Workspace/Users/{me}/ce_lab2"
w.workspace.mkdirs(PARENT)
print("warehouse:", WH, "| parent:", PARENT)

# COMMAND ----------

# MAGIC %md ## Step 1 · Create the baseline space (tables only) and score it

# COMMAND ----------

space_id = h.create_space(api, f"ce-lab2-{re.sub('[^a-z0-9]','-',me.split('@')[0])}", WH, PARENT, h.space_json())
print("space:", space_id)
baseline = h.run_suite(api, space_id)

# COMMAND ----------

# MAGIC %md ## Step 2 · Diagnose each failure from the generated SQL
# MAGIC For every FAIL below, answer: *what did Genie assume that the business does not?* Is it **vocabulary/definition**, a **calculation**, or a **missing table**?

# COMMAND ----------

for r in baseline["results"]:
    if not r["pass"]:
        print("Q:", r["question"], "| expected", r["expected"], "| got", r["got"])
        print(r["sql"], "\n")

# COMMAND ----------

# MAGIC %md ## Step 3 · Fix with the smallest correct control
# MAGIC Edit the arguments, re-score. Change **one control at a time** and note the score.
# MAGIC *Hint:* the data tells Genie what the columns contain; it cannot tell Genie your company's definitions.

# COMMAND ----------

INSTRUCTIONS = [
    "Total customers served by GridWorks is 1,000,000.",
    "SAIDI (minutes per customer) = SUM(customers_interrupted x outage minutes) / 1,000,000 total customers served, using unplanned outages only (is_planned = false).",
    "'Open' work orders means status IN ('open','in_progress'). 'Priority two' means P2, 'priority one' means P1.",
    "A critical feeder is an asset with is_critical_feeder = true. An asset is overdue for inspection when next_inspection_due_date is before the date stated in the question.",
]
MEASURES = [
    {"name": "SAIDI minutes", "alias": "saidi_minutes",
     "sql": "SUM(customers_interrupted * timestampdiff(MINUTE, event_start_ts, event_end_ts)) / 1000000"},
]
EXAMPLE_SQLS = [
    # TODO (stretch): (question, sql) for a high-value recurring report
]
SAMPLE_QUESTIONS = ["Show priority-two outages by region for the last 30 days."]

h.update_space(api, space_id, h.space_json(instructions=INSTRUCTIONS or None, measures=MEASURES or None,
                                           example_sqls=EXAMPLE_SQLS or None, sample_questions=SAMPLE_QUESTIONS))
tuned = h.run_suite(api, space_id)

# COMMAND ----------

# MAGIC %md ## Step 4 · Prove it
# MAGIC Target: **6/6**. Then answer in your notes:
# MAGIC 1. Which control fixed which failure, and why was that the right control?
# MAGIC 2. What would adding *more tables* have done? What would a *bigger model* have done?
# MAGIC 3. Which of your fixes is a **definition** (instruction) and which is a **calculation** (measure / trusted SQL)?

# COMMAND ----------

print("baseline:", baseline["passed"], "->", "tuned:", tuned["passed"], "of", tuned["total"])
assert tuned["passed"] > baseline["passed"], "No improvement yet: re-read the failing SQL in Step 2"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debrief
# MAGIC - **Exam link (Domain 2):** a Genie space with correct tables, descriptions and SQL still misreads business terms → **general instructions that define the vocabulary**, not more trusted SQL, sample questions, or a larger model.
# MAGIC - **Partner takeaway:** keep a test set per Genie space, and re-run it after every change. That is what "validate before production" means.
# MAGIC - **Genie Ontology (preview; verify status):** automatically infers and ranks context like this from your estate. You still certify the critical definitions: *model the head*.
