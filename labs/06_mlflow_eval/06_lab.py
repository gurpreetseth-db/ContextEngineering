# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 6 · Evaluation-driven context engineering with MLflow 3
# MAGIC **Time:** 55 min core · **Maps to exam:** Domain 4 (MLflow 3 experiment results, reliable configuration), Domain 2 (prompt cost vs performance)
# MAGIC **Tiers:** *Core* = every `TODO`. *Skip-ahead* = `labs/solutions/06_mlflow_eval_solution`. *Stretch* = add an LLM-judge scorer and compare it to your code scorers.
# MAGIC Four context configurations, one test set, balanced-reliability selection.
# MAGIC > Illustrative: tested with `mlflow 3.17.2`, `databricks-openai 0.18.0`, `databricks-ai-search 0.81` on serverless **environment 4**.
# MAGIC > Scorer imports and dataset schema change between MLflow versions: verify against your installed version.

# COMMAND ----------

# MAGIC %pip install -q mlflow==3.17.2 databricks-openai==0.18.0 databricks-ai-search==0.81 pandas

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
dbutils.widgets.text("endpoint", "gurpreetsethi-vs-endpoint")
dbutils.widgets.text("model", "system.ai.claude-haiku-5-5")      # cheap, governed model service; resolve from your workspace
import re, json
import mlflow, pandas as pd
from mlflow.genai.scorers import scorer
from databricks_openai import DatabricksOpenAI
from databricks.ai_search.client import AISearchClient
from databricks.sdk import WorkspaceClient

CAT, SH = dbutils.widgets.get("catalog"), dbutils.widgets.get("shared_schema")
ENDPOINT, MODEL = dbutils.widgets.get("endpoint"), dbutils.widgets.get("model")
me = WorkspaceClient().current_user.me().user_name
LS = "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())
IDX = f"{CAT}.{LS}.doc_chunks_merged_index"          # built in Lab 3
mlflow.set_experiment(f"/Users/{me}/ce_lab6_context_eval")
mlflow.openai.autolog()                                 # every LLM call becomes a trace
llm = DatabricksOpenAI(use_ai_gateway=True)             # routed through Unity AI Gateway; no keys in code
index = AISearchClient().get_index(endpoint_name=ENDPOINT, index_name=IDX)
print("mlflow", mlflow.__version__, "| index", IDX, "| model", MODEL)

# COMMAND ----------

# MAGIC %md ## Step 1 · The business task and the failure modes we are testing
# MAGIC Control-room staff need **current, regionally correct** procedures. Failure modes: superseded/draft content used as fact (poisoning/clash), wrong region (confusion), unsupported answers (no grounding), and cost.

# COMMAND ----------

# MAGIC %md ## Step 2 · A representative dataset (with traps)

# COMMAND ----------

DATA = [
 {"inputs": {"question": "What must happen when isolating a critical 33kV feeder?", "region": "VIC"},
  "expectations": {"source": "PRC-LOTO-001", "facts": ["second competent person", "witness"]}},
 {"inputs": {"question": "Who must witness 33kV isolations?", "region": "NSW"},
  "expectations": {"source": "PRC-LOTO-002", "facts": ["all 33kV isolations"]}},
 {"inputs": {"question": "What is the minimum vegetation clearance for 33kV in bushfire-prone areas?", "region": "VIC"},
  "expectations": {"source": "PRC-VEG-010", "facts": ["3.0 m"]}},
 {"inputs": {"question": "A transformer scores 45. Which health band is that and how soon must it be reinspected?", "region": "VIC"},
  "expectations": {"source": "PRC-XFMR-020", "facts": ["poor", "180"]}},
 {"inputs": {"question": "What defines a priority two outage?", "region": "SA"},
  "expectations": {"source": "PRC-SAFE-030", "facts": ["500 customers", "critical feeder"]}},
 {"inputs": {"question": "How is SAIDI calculated and are planned outages included?", "region": "QLD"},
  "expectations": {"source": "PRC-SAIDI-040", "facts": ["reported separately"]}},
 {"inputs": {"question": "What is the earth resistance limit?", "region": "VIC"},          # trap: only a DRAFT exists
  "expectations": {"refusal": True}},   # no "source" key: MLflow rejects None expectation values
 {"inputs": {"question": "What caused the authentication failures after certificate rotation?", "region": "NSW"},
  "expectations": {"source": "INC-2026-017", "facts": ["old intermediate certificate"]}},
]
print(len(DATA), "cases, including 1 trap where the only matching document is an unapproved draft")

# COMMAND ----------

# MAGIC %md ## Step 3 · The agent, with the context levers as configuration

# COMMAND ----------

COLS = ["chunk_id", "document_id", "region_code", "status", "text"]
SYSTEM = "You are the GridWorks operations assistant. Answer ONLY from the evidence. Cite chunk ids in square brackets, e.g. [PRC-LOTO-001#00]."
STRICT = " If the evidence does not answer the question, reply exactly: INSUFFICIENT EVIDENCE."

CONFIGS = {
  "A_baseline":        {"governed": False, "k": 6, "strict": False},
  "B_governed":        {"governed": True,  "k": 4, "strict": False},
  "C_governed_small":  {"governed": True,  "k": 2, "strict": False},
  "D_governed_strict": {"governed": True,  "k": 3, "strict": True},
}

def answer_text(content) -> str:
    """Some model services return a LIST of content blocks (a `reasoning` block, then `text`).
    Keep only the text; never store or score the reasoning block (do not preserve hidden chain-of-thought)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""

def make_agent(cfg):
    def predict(question: str, region: str):
        filters = {"status": "current", "region_code": [region, "ALL"]} if cfg["governed"] else None
        res = index.similarity_search(query_text=question, columns=COLS, filters=filters, num_results=cfg["k"])
        rows = [dict(zip(COLS, r[:len(COLS)])) for r in res["result"]["data_array"]]
        evidence = "\n\n".join(f"[{r['chunk_id']}] {r['text']}" for r in rows)
        out = llm.chat.completions.create(model=MODEL, max_tokens=800,   # NB: some model services reject `temperature`
             messages=[
            {"role": "system", "content": SYSTEM + (STRICT if cfg["strict"] else "")},
            {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{evidence}"}])
        return {"answer": answer_text(out.choices[0].message.content), "retrieved": [{k: r[k] for k in COLS[:4]} for r in rows],
                "context_chars": len(evidence)}
    return predict

# COMMAND ----------

# MAGIC %md ## Step 4 · Scorers: one per failure mode (deterministic, so results are repeatable)

# COMMAND ----------

@scorer
def context_recall(outputs, expectations):
    """Did retrieval surface the authoritative source?  Return 1.0/0.0. (No `source` key => nothing to recall => 1.0)"""
    # TODO
    raise NotImplementedError

ABSENCE = re.compile(r"(does not|do not|doesn't|not (state|contain|specify|provide|include)|no approved|insufficient|cannot|can't|unable)", re.I)

@scorer
def answer_correct(outputs, expectations):
    a = outputs["answer"]
    if expectations.get("refusal"):
        # Correct = signals the information is absent AND does not assert the draft figure as fact.
        asserts_draft_as_fact = bool(re.search(r"\b5\s*(ohm|\u03a9)", a, re.I)) and not re.search(r"(draft|proposed|not approved|not yet in force)", a, re.I)
        return float(bool(ABSENCE.search(a)) and not asserts_draft_as_fact)
    return float(all(f.lower() in a.lower() for f in expectations["facts"]))

@scorer
def grounded_citations(outputs, expectations):
    cited = set(re.findall(r"\[([A-Za-z0-9\-]+#\d+)\]", outputs["answer"]))
    have = {r["chunk_id"] for r in outputs["retrieved"]}
    if expectations.get("refusal") and not cited:
        return 1.0
    return float(bool(cited) and cited <= have)

@scorer
def authority_safe(outputs, inputs):
    """No superseded/draft or wrong-region content reached the context. Each retrieved row has status and region_code."""
    # TODO: the context-level metric. Output quality alone can look fine while the context is contaminated.
    raise NotImplementedError

SCORERS = [context_recall, answer_correct, grounded_citations, authority_safe]
QUALITY = ["context_recall", "answer_correct", "grounded_citations", "authority_safe"]

# COMMAND ----------

# MAGIC %md
# MAGIC > **Lesson from building this lab.** An earlier version of `answer_correct` matched refusals with a short keyword list and scored the governed
# MAGIC > configs at 0.88. The trace showed the agent had refused *correctly* ("the evidence does not state…"); the scorer was wrong.
# MAGIC > **Always read the failing traces before you trust a metric** (loop step 8). Also note the baseline looked fine on answer quality while being fed
# MAGIC > superseded, draft and wrong-region chunks on almost every call: only the context-level scorer (`authority_safe`) exposed it.

# COMMAND ----------

# MAGIC %md ## Step 5 · Baseline, then change ONE lever at a time

# COMMAND ----------

results, ctx = {}, {}
for name, cfg in CONFIGS.items():
    with mlflow.start_run(run_name=name) as run:
        mlflow.log_params({"governed": cfg["governed"], "top_k": cfg["k"], "strict_prompt": cfg["strict"], "model": MODEL})
        ev = mlflow.genai.evaluate(data=DATA, predict_fn=make_agent(cfg), scorers=SCORERS)
        results[name] = ev.metrics
    print(name, {k: round(v, 3) for k, v in ev.metrics.items() if k.endswith("/mean")})

# COMMAND ----------

# MAGIC %md ## Step 6 · Compare on ALL required metrics, not on the average

# COMMAND ----------

def pick(m, name):   # tolerate "<metric>/mean" or "<metric>" metric naming across MLflow versions
    return m.get(f"{name}/mean", m.get(name))

table = pd.DataFrame({n: {q: pick(m, q) for q in QUALITY} for n, m in results.items()}).T
missing = table.columns[table.isna().any()].tolist()
if missing: print(f"WARNING Scorers produced no value for {missing}: a scorer raised on some row. Inspect the MLflow UI traces.")
table["mean"] = table[QUALITY].mean(axis=1)
table["worst_metric"] = table[QUALITY].min(axis=1)
# cost proxy: average characters of context per call (from a quick re-run of retrieval-only sizes)
for n, cfg in CONFIGS.items():
    ctx[n] = sum(make_agent(cfg)(d["inputs"]["question"], d["inputs"]["region"])["context_chars"] for d in DATA[:3]) / 3
table["avg_context_chars"] = pd.Series(ctx)
display(table.round(3))

# COMMAND ----------

# MAGIC %md
# MAGIC **Selection rule (state it before you look at the numbers):** a configuration is eligible only if **every** quality metric is at or above the threshold.
# MAGIC Among eligible configurations choose the cheapest context. Never pick on the highest mean or on one impressive metric.

# COMMAND ----------

# TODO: state your acceptance threshold BEFORE reading the table
THRESHOLD = 0.85
eligible = table[table["worst_metric"] >= THRESHOLD]
winner = eligible["avg_context_chars"].idxmin() if len(eligible) else None
best_by_mean = table["mean"].idxmax()
print("best by mean:", best_by_mean, "| eligible:", list(eligible.index), "| winner:", winner)

# COMMAND ----------

# MAGIC %md ## Checks

# COMMAND ----------

def check(n, ok): print(("PASS  " if ok else "FAIL  ") + n); return ok
res = [
  check("all four configurations were evaluated", len(results) == 4),
  check("every quality metric has a value for every configuration (no silent NaN)", not table[QUALITY].isna().any().any()),
  check("baseline (ungoverned) fails the authority check", table.loc["A_baseline", "authority_safe"] < 1.0),
  check("governed configurations never leak non-current/wrong-region context", (table.loc[["B_governed", "C_governed_small", "D_governed_strict"], "authority_safe"] == 1.0).all()),
  check("governance improved the worst metric over the baseline", table.loc["B_governed", "worst_metric"] > table.loc["A_baseline", "worst_metric"]),
  check("a winner was chosen by the all-metrics-above-threshold rule", winner is not None),
]
print("\nLab 6 complete. Winner:" if all(res) else "\nKeep going: fix the FAIL lines.", winner)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debrief
# MAGIC - The baseline's **answers** looked fine. What did only `authority_safe` reveal, and why would a mean-score or answer-only comparison have picked the wrong configuration?
# MAGIC - Which configuration would you ship, and what does "no metric lagging" mean for that decision? (Exam: parallel-coordinates chart, not mean, not spread, not the single best metric.)
# MAGIC - Open the MLflow UI: compare the four runs with the **parallel coordinates** chart and read one failing trace end to end.
# MAGIC - Production: sample live traffic through the same scorers and alert on `authority_safe` regressions.
