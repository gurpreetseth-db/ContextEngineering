# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Grants for the learner group (DRY RUN by default)
# MAGIC Least privilege on purpose, two audiences:
# MAGIC - **Learners** read everything in `ce_shared` *except* `ce_ground_truth` (they must inspect the messy tables to judge them in Lab 1).
# MAGIC - **The agent / app service principal** reads **certified assets only**. `raw_*`, `draft_*`, `derived_*` and `ce_ground_truth` are never granted to it.
# MAGIC
# MAGIC Set `apply=true` only after reviewing the printed statements. Never grant to `account users` on a shared production catalog.

# COMMAND ----------

dbutils.widgets.text("catalog", "gsethi")
dbutils.widgets.text("schema", "ce_shared")
dbutils.widgets.text("learners_group", "ce-learners")
dbutils.widgets.text("learners", "")   # comma-separated learner identities (emails), to pre-create their schemas
dbutils.widgets.text("agent_principal", "")  # service principal application id of the deployed app
dbutils.widgets.dropdown("apply", "false", ["false", "true"])
CAT, SH = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")
AGENT = dbutils.widgets.get("agent_principal")
LEARNERS = [x.strip() for x in dbutils.widgets.get("learners").split(",") if x.strip()]
GROUP, APPLY = dbutils.widgets.get("learners_group"), dbutils.widgets.get("apply") == "true"

CERTIFIED = ["gold_outage_events", "gold_asset_health", "gold_work_orders", "gold_crews",
             "gold_crew_availability", "procedure_documents"]

LEARNER_READ = CERTIFIED + ["raw_outage_events", "raw_inspection_export", "derived_outage_rollup_v1", "draft_outage_summary_wip"]

stmts = [
    f"GRANT USE CATALOG ON CATALOG {CAT} TO `{GROUP}`",
    f"GRANT USE SCHEMA ON SCHEMA {CAT}.{SH} TO `{GROUP}`",
    f"GRANT READ VOLUME ON VOLUME {CAT}.{SH}.docs TO `{GROUP}`",
] + [f"GRANT SELECT ON TABLE {CAT}.{SH}.{t} TO `{GROUP}`" for t in LEARNER_READ]
if AGENT:
    stmts += [f"GRANT USE CATALOG ON CATALOG {CAT} TO `{AGENT}`", f"GRANT USE SCHEMA ON SCHEMA {CAT}.{SH} TO `{AGENT}`",
              f"GRANT READ VOLUME ON VOLUME {CAT}.{SH}.docs TO `{AGENT}`"] + \
             [f"GRANT SELECT ON TABLE {CAT}.{SH}.{t} TO `{AGENT}`" for t in CERTIFIED]

import re

def schema_for(identity: str) -> str:
    """Same rule the labs use: ce_<local part of the identity>."""
    return "ce_" + re.sub(r"[^a-z0-9]", "_", identity.split("@")[0].lower())

# Two learners with the same local part (jo.smith@a.com, jo.smith@b.com) would share a schema: refuse.
names = {}
for who in LEARNERS:
    names.setdefault(schema_for(who), []).append(who)
clashes = {k: v for k, v in names.items() if len(v) > 1}
assert not clashes, f"Schema name collision, rename or split the cohort: {clashes}"

# Verified approach: the facilitator pre-creates each learner's schema and grants ALL PRIVILEGES on it.
# No catalog-level CREATE SCHEMA is needed (tested), which keeps the shared catalog locked down.
for who in LEARNERS:
    sch = schema_for(who)
    stmts += [f"CREATE SCHEMA IF NOT EXISTS {CAT}.{sch}", f"GRANT ALL PRIVILEGES ON SCHEMA {CAT}.{sch} TO `{who}`"]

for s in stmts:
    print(("APPLY  " if APPLY else "DRY    ") + s)
    if APPLY:
        spark.sql(s)

# COMMAND ----------

# MAGIC %md
# MAGIC **Gotchas**
# MAGIC - Lab 1 builds views, comments and tags in each learner's own schema, so learners never need write access to `ce_shared`.
# MAGIC - Tested on a non-admin principal: no catalog-level `CREATE SCHEMA` is needed when each learner's schema is pre-created (this notebook does it).
# MAGIC - Learners also need the workspace entitlements `workspace-access` and `databricks-sql-access`, and a Lakebase role: see `docs/learner_provisioning_runbook.md`.
# MAGIC - Untested with real learner identities (only one identity was available while building). Test with a non-admin before the session.
