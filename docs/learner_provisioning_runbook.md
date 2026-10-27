# Learner provisioning runbook (tested)

**Tested on 2026-10-28 on the Sydney workspace with ONE non-admin *service principal* acting as a learner.** It is not yet tested with a real human user or with 15 concurrent learners; see "Not tested" below. Replace `<learner>` with the learner's identity and `<schema>` with the schema name derived by the labs.

## 1. What a learner needs (the verified minimum)

| Layer | Grant | Why / what we saw |
|---|---|---|
| Workspace | Entitlements **`workspace-access`** and **`databricks-sql-access`** | Without them the API refuses: *"This API is disabled for users without the databricks-sql-access or workspace-access or workspace-consume entitlements."* |
| Workspace | `CAN_READ` on the folder holding the lab notebooks | Lets the learner open and run them |
| Unity Catalog | `USE CATALOG` on the catalog; `USE SCHEMA` on `ce_shared`; `READ VOLUME` on `ce_shared.docs` | |
| Unity Catalog | `SELECT` on the 10 tables learners may inspect: the 6 certified tables plus `raw_outage_events`, `raw_inspection_export`, `derived_outage_rollup_v1`, `draft_outage_summary_wip` | Lab 1 needs them to judge what is authoritative |
| Unity Catalog | **Not** `ce_ground_truth`; **not** `CREATE SCHEMA` on the catalog; **no** write on `ce_shared` | All verified as refused |
| Unity Catalog | Facilitator **pre-creates** the learner's schema `gsethi.<schema>` and runs `GRANT ALL PRIVILEGES ON SCHEMA gsethi.<schema> TO <learner>` | `CREATE SCHEMA IF NOT EXISTS` on an existing schema succeeded **without** catalog-level `CREATE SCHEMA` |
| Lakebase | A Postgres role for the learner, plus `GRANT CREATE ON DATABASE databricks_postgres TO "<role>"` | The lab creates its own Postgres schema and tables; nothing broader was needed |

### Statements (as run)
```sql
-- Unity Catalog (as the facilitator)
GRANT USE CATALOG ON CATALOG gsethi TO `<learner>`;
GRANT USE SCHEMA ON SCHEMA gsethi.ce_shared TO `<learner>`;
GRANT READ VOLUME ON VOLUME gsethi.ce_shared.docs TO `<learner>`;
GRANT SELECT ON TABLE gsethi.ce_shared.<each of the 10 tables> TO `<learner>`;
CREATE SCHEMA IF NOT EXISTS gsethi.<schema>;
GRANT ALL PRIVILEGES ON SCHEMA gsethi.<schema> TO `<learner>`;
```
```bash
# Lakebase role (service principal shown; CLI example from the product help)
databricks postgres create-role projects/<project>/branches/production \
  --role-id <valid-id> \
  --json '{"spec":{"identity_type":"SERVICE_PRINCIPAL","postgres_role":"<client-id>","auth_method":"LAKEBASE_OAUTH_V1"}}'
# then, as the project owner, in SQL:  GRANT CREATE ON DATABASE databricks_postgres TO "<client-id>";
```

## 2. Gotchas found while testing

| Gotcha | Detail |
|---|---|
| **`role_id` must start with a lowercase letter** | The CLI help example uses the client id as `--role-id`, but a client id starting with a digit fails the pattern `^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$`. Use any valid id (we used `ce-test-learner`) and put the real identity in `postgres_role`. |
| **`run_as` on a job needs `servicePrincipal.user`** | That role is managed at the **account** level, not the workspace permissions API ("`servicePrincipals` is not a supported object type"). Workaround used: authenticate as the principal itself (OAuth M2M, short-lived secret) and submit the job as it. Not relevant for human learners. |
| **Facilitators cannot drop a learner-owned Postgres schema** | `DROP SCHEMA` fails with *"must be owner of schema"* even for the project owner; `DROP OWNED BY` also fails. Have the learner (or the principal) drop its own schema, or use a superuser role. The deployed app's `ce_app` schema has the same ownership property. |
| **Schema naming collides on the local part** | The labs derive `ce_<email local part>`. `jo.smith@partnerA.com` and `jo.smith@partnerB.com` would collide. `02_grants` now refuses to run if two learners map to the same schema. |
| Environment | Use serverless **environment 4** and the pinned packages (`docs/00_fact_sheet.md` §9, §14). |

## 3. Not tested (state this to the client)
- A real **human** learner: `identity_type: USER` roles, email-shaped role names, and OAuth sign-in.
- **15 concurrent** learners (warehouse, AI Search endpoint, Lakebase connection limits).
- Group-based grants (`ce-learners`): the principal was granted individually.
- Lab 3 (AI Search index creation) and Lab 6 (model access) as a non-admin.
- Row/column-level security.

## 4. Teardown (verified order)
1. Revoke Unity Catalog grants; `DROP SCHEMA gsethi.<schema> CASCADE`.
2. The learner's own principal drops its Postgres schema.
3. `REVOKE CREATE ON DATABASE databricks_postgres FROM "<role>"`; `databricks postgres delete-role …`.
4. Delete the principal (this also invalidates its secrets).
5. Check `SHOW GRANTS ON SCHEMA gsethi.ce_shared` for strays.
