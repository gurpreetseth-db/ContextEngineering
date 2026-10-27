# Context Engineering on Databricks: partner enablement kit

A facilitator-ready kit for teaching **Context Engineering** to experienced AI engineers: three 3.5-hour sessions, six hands-on labs plus a security lab, a deployable app, decks with speaker notes, an assessment pack, and a facilitator guide.

> **Course promise.** Give the agent the right context, at the right time, in the smallest useful form, from governed sources, and prove the choice with evaluation.

This is community enablement material. It is **not** an official Databricks course or documentation, and it does **not** guarantee a certification outcome. Code is illustrative: product names, SDKs and preview status change quickly, so verify them against current documentation before use.

## What is in the kit

| Folder | What it is |
|---|---|
| `facilitator-guide/` | Run-of-show for three 210-minute sessions, risks and fallbacks, exam alignment, ANZ considerations, scenario-swap table |
| `slides/` | Three self-contained HTML decks (48 slides), speaker notes on **N**. See `slides/README.md` |
| `labs/` | Learner notebooks and runnable solutions: UC curation, Genie tuning, AI Search, Lakebase memory, injection/poisoning, MLflow evaluation, and the app lab guide |
| `app/` | An AppKit (Node/React) assistant: governed retrieval, durable memory, an approval gate |
| `data/` | A deterministic generator for the fictional "ANZ GridWorks" dataset (no real data) |
| `assessment/` | Parallel pre/post quiz forms (original questions), answer key, capstone rubric |
| `docs/` | `00_fact_sheet.md` (verified facts and gotchas) and `learner_provisioning_runbook.md` |

## The running scenario
A fictional electricity-network operator. The assistant answers outage and maintenance questions over certified tables, retrieves safety procedures, remembers preferences, and drafts maintenance requests that need a human to approve. The scenario is swappable (see the guide).

## What was verified, and what was not
Verified on **one** Databricks workspace (Sydney), serverless **environment 4**:
- Labs 1, 2, 3, 4, 6 and the injection lab run end to end; Labs 1 and 4 also pass as a **non-admin** principal with a refusal test.
- The app was deployed, exercised through its API, and driven in a real browser (several UI defects were found and fixed this way).
- Every slide passes overflow and WCAG AA contrast checks at two resolutions.

**Not verified:** a human (non-service-principal) learner, 15 concurrent learners, group-based grants, Labs 3 and 6 as a non-admin, the app's on-behalf-of-user mode, and projector display. Every number shown on a slide is a measured result from one model and small samples, so re-measure on yours.

## Getting started
1. Read `docs/00_fact_sheet.md` (product names, pins, gotchas) and `docs/learner_provisioning_runbook.md`.
2. Run `labs/00_setup/01_load_gridworks` to create the shared schema. Defaults such as the `catalog` and `endpoint` widgets point at the author's test workspace: **set them to yours**.
3. Use serverless **environment 4** and the pinned package versions in the fact sheet. (A newer `psycopg` 3.3.x binary crashes at import on environments 3 and 4.)
4. Open the decks in `slides/` in a browser. Rebuild them with `python3 slides/_build/build.py`.
5. The app needs placeholders in `app/ce-gridworks-assistant/databricks.yml` filled in (workspace host, warehouse id, index name) before it can be deployed.

## Licence and attribution
No licence has been chosen yet; until one is added, all rights are reserved by the author. The Databricks logo files used in the decks come from Databricks' slide brand resources and remain Databricks' property. The exam facts summarise the publicly available exam guide; check the live guide before relying on them.
