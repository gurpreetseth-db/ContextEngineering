# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 4 · Durable state and memory on Lakebase
# MAGIC **Time:** 45 min core · **Maps to exam:** Domain 4 (Lakebase memory, Delta/Lakebase state vs scratchpad, structured vs semantic memory)
# MAGIC **Tiers:** *Core* = every `TODO`. *Skip-ahead* = `labs/solutions/04_lakebase_memory_solution`. *Stretch* = Step 7.
# MAGIC
# MAGIC A resumable GridWorks investigation: checkpoint every step, pause for human approval, survive a "process restart",
# MAGIC keep cross-session preferences, and make the side effect idempotent.
# MAGIC > Illustrative: LangGraph / Lakebase APIs move quickly. Tested with `langgraph 1.2.18`, `langgraph-checkpoint-postgres 3.2.0`, `psycopg 3.2.13`. Verify your installed versions.

# COMMAND ----------

# MAGIC %pip install -q "langgraph==1.2.18" "langgraph-checkpoint-postgres==3.2.0" "psycopg[binary,pool]==3.2.13"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("shared_schema", "ce_shared")
dbutils.widgets.text("lakebase_endpoint", "projects/ce-enablement/branches/production/endpoints/primary")
dbutils.widgets.text("pg_database", "databricks_postgres")
import re, json, uuid
from collections import Counter
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
me = w.current_user.me().user_name
CAT, SH = dbutils.widgets.get("catalog"), dbutils.widgets.get("shared_schema")
EP, PGDB = dbutils.widgets.get("lakebase_endpoint"), dbutils.widgets.get("pg_database")
PGSCHEMA = "ce_" + re.sub(r"[^a-z0-9]", "_", me.split("@")[0].lower())   # one Postgres schema per learner
api = lambda m, p, b=None: w.api_client.do(m, p, body=b) or {}
HOST = api("GET", f"/api/2.0/postgres/{EP}")["status"]["hosts"]["host"]
print("host:", HOST, "| pg schema:", PGSCHEMA)

# COMMAND ----------

# MAGIC %md ## Step 1 · Connect to Lakebase with a short-lived OAuth credential (never a stored password)

# COMMAND ----------

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

def conninfo():
    tok = api("POST", "/api/2.0/postgres/credentials", {"endpoint": EP})["token"]   # ~1h; mint per pool
    return (f"host={HOST} port=5432 dbname={PGDB} user={me} password={tok} sslmode=require "
            f"options='-c search_path={PGSCHEMA},public'")

async def new_pool():
    # the checkpointer requires autocommit + dict rows
    pool = AsyncConnectionPool(conninfo(), min_size=1, max_size=4, open=False,
                               kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row})
    await pool.open()
    return pool

# schema must exist before search_path points at it
import psycopg
with psycopg.connect(conninfo().replace(f"options='-c search_path={PGSCHEMA},public'", ""), autocommit=True) as c:
    c.execute(f'CREATE SCHEMA IF NOT EXISTS "{PGSCHEMA}"')
    print("schema ready:", c.execute("select current_user").fetchone())

# COMMAND ----------

# MAGIC %md ## Step 2 · Long-term memory: preferences that survive sessions (structured, exact)
# MAGIC Exact keys (user, key) → a **structured query**, not semantic search. Upsert so repeats are safe.

# COMMAND ----------

pool = await new_pool()
async with pool.connection() as c:
    await c.execute("""CREATE TABLE IF NOT EXISTS user_prefs (
        user_id text, key text, value text, updated_at timestamptz DEFAULT now(), PRIMARY KEY (user_id, key))""")
    await c.execute("""CREATE TABLE IF NOT EXISTS maintenance_requests (
        work_order_id int PRIMARY KEY, asset_id text, summary text, approved_by text, created_at timestamptz DEFAULT now())""")

async def set_pref(user, key, value):
    # TODO: UPSERT into user_prefs so that repeating the call is safe (INSERT ... ON CONFLICT (user_id,key) DO UPDATE ...)
    raise NotImplementedError

async def get_pref(user, key):
    # TODO: exact lookup by (user_id, key) -> value or None.   Why a structured query and not AI Search?
    raise NotImplementedError

await set_pref(me, "response_format", "concise bullet points")
print("stored preference:", await get_pref(me, "response_format"))

# COMMAND ----------

# MAGIC %md ## Step 3 · The workflow: checkpoint after every step, pause for human approval

# COMMAND ----------

from typing import TypedDict, Annotated, Optional
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

EXEC = Counter()   # counts how many times each node actually ran (proves "no re-run after restart")

class S(TypedDict):
    work_order_id: int
    log: Annotated[list, add]          # compact, user-visible progress only: no raw tool payloads
    asset_id: Optional[str]
    health_band: Optional[str]
    draft: Optional[dict]
    approved_by: Optional[str]

def fetch_work_order(s: S):
    EXEC["fetch_work_order"] += 1
    r = spark.sql(f"SELECT asset_id, status FROM {CAT}.{SH}.gold_work_orders WHERE work_order_id = {s['work_order_id']}").first()
    return {"asset_id": r.asset_id, "log": [f"work order {s['work_order_id']} -> asset {r.asset_id} ({r.status})"]}

def check_asset(s: S):
    EXEC["check_asset"] += 1
    r = spark.sql(f"SELECT health_band, health_score FROM {CAT}.{SH}.gold_asset_health WHERE asset_id = '{s['asset_id']}'").first()
    return {"health_band": r.health_band, "log": [f"asset health {r.health_band} ({r.health_score})"]}

def draft_request(s: S):
    EXEC["draft_request"] += 1
    # TODO: return {"draft": {...asset_id, summary...}, "log": [...]}. Keep saved state compact (no raw payloads).
    raise NotImplementedError

def approval_gate(s: S):
    EXEC["approval_gate"] += 1
    # TODO: pause for a human with langgraph.types.interrupt({...}). The resume value is the decision dict {"approve": bool, "by": str}.
    #       Return {"approved_by": <who or None>, "log": [...]}
    raise NotImplementedError

async def finalize(s: S):
    EXEC["finalize"] += 1
    if s.get("approved_by"):
        async with pool.connection() as c:       # idempotent side effect: safe to retry
            await c.execute("""INSERT INTO maintenance_requests(work_order_id,asset_id,summary,approved_by)
                               VALUES (%s,%s,%s,%s) ON CONFLICT (work_order_id) DO NOTHING""",
                            (s["work_order_id"], s["draft"]["asset_id"], s["draft"]["summary"], s["approved_by"]))
    return {"log": ["finalized" if s.get("approved_by") else "rejected: nothing written"]}

def build(checkpointer):
    g = StateGraph(S)
    for n, f in [("fetch_work_order", fetch_work_order), ("check_asset", check_asset), ("draft_request", draft_request),
                 ("approval_gate", approval_gate), ("finalize", finalize)]:
        g.add_node(n, f)
    g.add_edge(START, "fetch_work_order"); g.add_edge("fetch_work_order", "check_asset"); g.add_edge("check_asset", "draft_request")
    g.add_edge("draft_request", "approval_gate"); g.add_edge("approval_gate", "finalize"); g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)

checkpointer = AsyncPostgresSaver(pool)
# TODO: create the checkpoint tables (await ...). Exam question: is this call synchronous or awaited in an async environment?
graph = build(checkpointer)   # compiles with graph.compile(checkpointer=checkpointer)
WO = 1042
THREAD = f"wp-{WO}-{uuid.uuid4().hex[:6]}"      # durable work-package id
cfg = {"configurable": {"thread_id": THREAD}}

# COMMAND ----------

out = await graph.ainvoke({"work_order_id": WO, "log": []}, cfg)
snap = await graph.aget_state(cfg)
paused_at = snap.next
print("paused at:", snap.next, "| interrupts:", [i.value["question"] for i in snap.tasks[0].interrupts])
print("executed so far:", dict(EXEC))

# COMMAND ----------

# MAGIC %md ## Step 4 · Simulate a process restart, then resume from Lakebase
# MAGIC Throw away the pool, checkpointer and graph. Rebuild them from scratch. The thread id is all we keep.

# COMMAND ----------

await pool.close()
del graph, checkpointer, pool
EXEC.clear()

pool = await new_pool()
checkpointer = AsyncPostgresSaver(pool)
# TODO: re-create the tables safely (is setup() idempotent?) and rebuild the graph
graph = build(checkpointer)

snap = await graph.aget_state(cfg)
print("after 'restart', state recovered from Lakebase:", snap.values["log"])
# TODO: resume the SAME thread with Command(resume={"approve": True, "by": me})
final = None
print("executed after resume:", dict(EXEC))
print("final log:", final and final["log"])

# COMMAND ----------

# MAGIC %md ## Step 5 · Idempotency: resuming twice must not duplicate the side effect

# COMMAND ----------

async with pool.connection() as c:
    await c.execute("""INSERT INTO maintenance_requests(work_order_id,asset_id,summary,approved_by)
                       VALUES (%s,%s,%s,%s) ON CONFLICT (work_order_id) DO NOTHING""", (WO, "x", "retry", me))
    cur = await c.execute("SELECT count(*) AS n FROM maintenance_requests WHERE work_order_id=%s", (WO,))
    n = (await cur.fetchone())["n"]
print("rows for work order", WO, "=", n)

# COMMAND ----------

# MAGIC %md ## Step 6 · Use the *nearest valid* memory source
# MAGIC Current explicit instruction beats older long-term memory. Session state beats a lookup of something already in the session.

# COMMAND ----------

def resolve_format(session_instruction, long_term_pref):
    return session_instruction or long_term_pref or "default"

fmt_today = resolve_format("a numbered table", await get_pref(me, "response_format"))
fmt_default = resolve_format(None, await get_pref(me, "response_format"))
print("today:", fmt_today, "| default:", fmt_default)

# COMMAND ----------

# MAGIC %md ## Step 7 · Stretch
# MAGIC Which of these belong in the saved graph state, which in `user_prefs`, which in a Delta table, and which should be discarded?
# MAGIC raw SQL result rows · the user's preferred format · the approval decision · a 10 MB tool payload · the draft request · "similar past incidents" lookups.

# COMMAND ----------

# MAGIC %md ## Checks

# COMMAND ----------

def check(n, ok): print(("PASS  " if ok else "FAIL  ") + n); return ok
res = [
  check("graph paused at the approval gate before the restart", paused_at == ("approval_gate",)),
  check("after restart, earlier steps were NOT re-executed", EXEC["fetch_work_order"] == 0 and EXEC["check_asset"] == 0 and EXEC["draft_request"] == 0),
  check("approval ran on resume and finalize executed once", EXEC["finalize"] == 1),
  check("exactly one maintenance request row (idempotent)", n == 1),
  check("long-term preference persisted", (await get_pref(me, "response_format")) == "concise bullet points"),
  check("explicit session instruction overrides older preference", fmt_today == "a numbered table" and fmt_default == "concise bullet points"),
  check("no raw tool payloads in saved state", final is not None and all(len(x) < 200 for x in final["log"])),
]
await pool.close()
print("\nLab 4 complete." if all(res) else "\nKeep going: fix the FAIL lines.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debrief
# MAGIC - **Exam link (Domain 4):** async LangGraph on Lakebase → `AsyncPostgresSaver(pool)`, `await checkpointer.setup()`, `compile(checkpointer=...)`.
# MAGIC - Scratchpad vs durable state: what had to survive the restart, and what would have been lost in an in-context scratchpad?
# MAGIC - A larger context window would not have helped. Why?
