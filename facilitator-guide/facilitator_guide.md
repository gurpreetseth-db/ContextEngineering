# Context Engineering on Databricks: Facilitator Guide
**ANZ C&SI partner enablement · 10.5 contact hours · seasoned AI engineers**

> **Course promise.** Give the agent the right context, at the right time, in the smallest useful form, from governed sources, and prove the choice with evaluation.

**Status of this guide:** built and tested against a Sydney (ap-southeast-2) workspace on 2026-10-27/28. Every claim marked **VERIFY** must be re-checked before delivery. Product names, preview status, SDK versions and exam facts move quickly; `docs/00_fact_sheet.md` is the source of truth and wins over this file if they disagree.

---

## 1. At a glance

| | |
|---|---|
| **Audience** | AI engineers, solution architects, lead developers, delivery leads at consulting and systems-integration partners in ANZ |
| **Prerequisites** | Python + SQL, LLM/RAG/tool-calling basics, notebook fluency. No Databricks Genie, AI Search or Lakebase experience assumed |
| **Format** | 3 × 3.5 h sessions. Works live, virtual, or self-paced (every lab has three tiers: core, skip-ahead, stretch) |
| **Cohort size** | Designed for up to 15 learners |
| **Running scenario** | **ANZ GridWorks Operations Assistant** (an electricity-network operator). Swap guide in §12 |
| **Labs** | 6 labs, 5 h of the 10.5 h. Capstone is a short in-session design review plus a take-home |
| **Slides** | `slides/`: three HTML decks (one per session) with speaker notes (press N) |
| **Exam** | Aligned to the *Databricks Certified Context Engineer Associate* (7 domains). This is **not** an official certification course and does not guarantee a pass |

### Learning outcomes
By the end, participants can:
1. Explain context engineering as a *systems* discipline, not prompt writing, and diagnose poisoning, distraction, confusion and clash from a trace.
2. Choose between Unity Catalog, Genie, AI Search, Delta, Lakebase, MCP, Agent Skills, the AI Gateway, Apps and MLflow by the *information problem*, not by product.
3. Curate governed context (authority, metadata, PII, least privilege) and write it down as a context contract.
4. Tune a Genie space with the *smallest correct control* and prove it with a test set.
5. Build governed retrieval (chunking, filters, freshness) and fix a stale index with the minimal change.
6. Put durable state and per-user memory on Lakebase, with a human approval gate and idempotent side effects.
7. Compare context configurations with MLflow on *balanced* reliability, including a context-level metric.
8. Reason through exam-style scenarios: requirement → evidence → constraint → minimal fix.

---

## 2. The teaching spine (use it in every module)

Ask the same five questions about every design decision:

| # | Question | Typical wrong answer to challenge |
|---|---|---|
| 1 | **Need.** What does the agent actually need for this decision? | "Give it everything" |
| 2 | **Timing.** When should it enter context: before inference, just in time, or after an intermediate result? | Loading it all up front |
| 3 | **Authority.** Which source is authoritative, permitted and fresh? | "Whatever retrieval returns" |
| 4 | **Efficiency.** How do we cut tokens, ambiguity, staleness, duplication? | "A bigger model or window" |
| 5 | **Proof.** Which trace, metric or business outcome shows the change helped? | "It looked better" |

**House rule:** never accept "use a larger model" as a first answer unless a trace proves capacity, not context quality, is the limit.

---

## 3. Schedule (re-timed against the real labs)

Lab durations are *core* tiers. The initial draft plan gave Lab 3 45 minutes and Lab 4 35; testing showed those were too short, so labs now total 300 minutes.

### Session 1 · Foundations, governance and Genie (210 min)
| Time | Segment | Method |
|---|---|---|
| 0:00 to 0:15 | Framing: model intelligence vs system reliability | Story + partner discussion |
| 0:15 to 0:50 | Mental model, failure modes, **reasoning modes**, attention budget | Whiteboard + trace diagnosis |
| 0:50 to 1:10 | The Databricks context stack by job | Architecture walkthrough |
| 1:10 to 1:20 | Break | |
| 1:20 to 2:10 | **Lab 1** · UC curation (50) | Notebook |
| 2:10 to 2:55 | **Lab 2** · Genie tuning (45) | Notebook + test set |
| 2:55 to 3:10 | System prompt and few-shot selection (Domain 2) | Short exercise |
| 3:10 to 3:30 | Debrief + exam practice | Scenario questions |

### Session 2 · Retrieval, memory, tools, compaction (210 min)
| Time | Segment | Method |
|---|---|---|
| 0:00 to 0:25 | Retrieval design: pre-inference vs just-in-time, chunking, freshness | Design exercise |
| 0:25 to 1:20 | **Lab 3** · AI Search (55) | Notebook |
| 1:20 to 1:30 | Break | |
| 1:30 to 2:00 | Memory architecture: lifetimes, Lakebase vs scratchpad, structured vs semantic | Architecture + code walk |
| 2:00 to 2:45 | **Lab 4** · Lakebase memory (45) | Notebook |
| 2:45 to 3:10 | Tool design, MCP, progressive disclosure, Agent Skills | Tool-schema refactor |
| 3:10 to 3:30 | Compaction and trimming | Trace surgery |

### Session 3 · Multi-agent, runtime, apps, evaluation (210 min)
| Time | Segment | Method |
|---|---|---|
| 0:00 to 0:20 | Multi-agent and long-horizon design | Boundary exercise |
| 0:20 to 0:45 | Unity AI Gateway: runtime governance | Architecture + live console |
| 0:45 to 0:55 | Break | |
| 0:55 to 1:45 | **Lab 5** · App-backed agent (50) | Guided app + review |
| 1:45 to 2:40 | **Lab 6** · MLflow evaluation (55) | Notebook |
| 2:40 to 3:10 | Capstone: design review (30) | Team presentations |
| 3:10 to 3:30 | Exam readiness + action plan | Discussion |

> **Lab 3b fits inside Session 2:** it runs as a 15-minute facilitator demo within §6.3 (taken from the memory slot); the full lab is self-paced or take-home. It is *not* added to the 630-minute total.

> **Risk: Session 3 is the tightest.** If the cohort is slow in Lab 6, move the capstone to a take-home and run the 30 minutes as an async review. Offer a **4 h extended Session 3** if the budget allows. Do not cut Lab 6: the context-contamination finding is the course's strongest result.

### Self-paced path
Run labs in order using the skip-ahead notebooks (`labs/solutions/`) to unblock, then read the *Debrief* at the end of each lab. Budget about 8 h.

---

## 4. Pre-course setup (do this two weeks out)

### Workspace
- [ ] Serverless **environment version 4** for every notebook. **Environment 2 hangs installing `mlflow` 3.x (25+ min).** Environments 3 and 4 install in about 75 s.
- [ ] Pin packages: `mlflow==3.17.2`, `databricks-openai==0.18.0`, `databricks-ai-search==0.81`, `langgraph==1.2.18`, `langgraph-checkpoint-postgres==3.2.0`, `psycopg[binary,pool]==3.2.13`. **VERIFY** latest versions at delivery.
- [ ] Run `labs/00_setup/01_load_gridworks` to create `gsethi.ce_shared` (11 tables, 12 documents). Re-point `catalog` if you use another catalog.
- [ ] Provision learners by `docs/learner_provisioning_runbook.md` (**tested with one non-admin service principal**: entitlements, Unity Catalog grants, pre-created schema, Lakebase role). Run `labs/00_setup/02_grants` with `apply=false` first and review the statements. **Still untested with a real human user and with 15 concurrent learners.**
- [ ] SQL warehouse warm (serverless starter auto-starts; first query can take minutes).
- [ ] An AI Search endpoint with capacity for ~15 indexes, and the embedding endpoint `databricks-gte-large-en`.
- [ ] A Lakebase project and one Postgres role per learner (see §10). The project used in testing is `ce-enablement`.
- [ ] Model service access: `system.ai.claude-haiku-5-5` (or your approved model) for Labs 5 and 6. The model name is configuration, not code.

### Rehearsal (non-negotiable)
Run **every solution notebook** (`labs/solutions/`) as a **learner identity, not an admin**, the day before. In testing, each lab hid at least one integration trap (§11).

### Pre-create slow things
AI Search index creation and the stale-index sync take minutes. Pre-create one *reference* index per learner group, and let learners create their own during the talk segments.

### Learners (send a week ahead)
Workspace access check, a 5-minute notebook warm-up, and the recommended Academy courses from the exam guide. Ask them to bring one real agent failure they have seen.

---

## 5. Session 1 · Foundations, governance and Genie

### 5.1 Framing (15 min)
**Message:** AI does not have an intelligence problem, it has a context problem. Reliability comes from the information environment.
- Ask the room: "Describe an agent failure from your last project." Collect on a board, then sort it by the four failure modes later in the session.
- Define **context**: everything available to the model at inference: instructions, user turn and history, few-shot examples, retrieved documents/rows/SQL results, tool names/schemas/outputs, scratchpad, long-term memory, compacted summaries, other agents' messages.
- Prompt engineering shapes instructions and demonstrations. Context engineering manages *selection, timing, authority, scope, persistence, compression, propagation, governance and evaluation*.

### 5.2 Mental model, failure modes, reasoning modes (35 min)
**Four failure modes: teach with trace signals and smallest-first fixes**

| Mode | Meaning | Trace signal | First response |
|---|---|---|---|
| **Poisoning** | Wrong information enters context and persists | A false fact is reused repeatedly | Remove/correct the source; stop it being retrieved or persisted |
| **Distraction** | Valid but excess context drowns the task | Quality drops as history/tool output grows | Scope, clear, retrieve later, compact |
| **Confusion** | Wrong context, memory, source or tool is *used* | Relevant options exist; the wrong one is chosen | Reduce candidates; sharpen metadata/descriptions |
| **Clash** | Context elements disagree | Conflicting instructions/definitions/memories | Set precedence and one source of truth |

Also name **context rot** (past a point, more tokens hurt, non-uniformly) and **context exhaustion**. Attention degrades *before* the hard window limit.

**Exercise: trace diagnosis (15 min, groups of 3).** Give each group four short traces. Ask: name the failure, cite the evidence, propose the smallest fix. Suggested set:
1. A stale address is repeatedly pulled from long-term memory → *poisoning*.
2. 100 pages of valid logs bury the latest constraint → *distraction*.
3. A prior-session licensing agreement leaks into a current contract answer → *confusion* (see the exam note below).
4. Two equally authoritative policies give different escalation rules → *clash*.

> **Exam note (official sample Q1).** Irrelevant prior-session content that gets *used* in a new answer is **confusion**, not poisoning. Poisoning requires incorrect information to corrupt later reasoning. Expect the room to argue; let them.

**Reasoning modes (Domain 1, easy points).** Standard for routine decisions and tool use; extended thinking when planning complexity gives a *measured* quality gain that justifies the tokens; reduced thinking for classification, routing and extraction where latency and cost matter. Tie it to token budget and context pressure.

**Plant the Lab 6 seed:** "Hold on to this: an agent can give a correct answer while being fed contaminated context. We will measure it."

### 5.3 The Databricks context stack by job (20 min)
Teach by *job*, not product tour.

| Job to be done | Capability | One-line message |
|---|---|---|
| Govern data, tools, metadata, permissions, lineage, PII | Unity Catalog | Can the agent see it, is it authoritative, is it allowed? |
| Semantic retrieval over documents | **Databricks AI Search** (formerly Vector Search) | Find by meaning, then filter by authority, freshness, scope |
| Natural-language analytics on curated data | **Genie** (Genie One and Genie Agents are generally available per the 16 Jun 2026 blog) | Ask governed data using business semantics |
| Reusable business meaning | UC semantics, metric views, domains, glossary; **Genie Ontology** | "Model the head": certify the critical definitions, let the platform infer the tail. **Genie Ontology is a preview capability (verify current status); label it on every slide and do not present it as a commitment** |
| Durable operational memory | Lakebase | Remember across sessions, support concurrency, audit |
| Durable analytic history | Delta tables | Governed, queryable history |
| Tool/data connectivity | MCP | Discover and call tools through a standard protocol |
| Rarely used instructions | Agent Skills | Pay tokens on demand |
| Runtime governance | Unity AI Gateway | Access, routing, budgets, guardrails, logging |
| Delivery surface | Databricks Apps | Identity, resource bindings, approvals, telemetry |
| Trace, evaluate, monitor | MLflow 3 | Prove it works |

**Architecture prompt:** "Where should this information live if it must survive a restart, be shared by several workers, be auditable, and not consume prompt tokens?" Expected: durable governed state, not a scratchpad.

### 5.4 Lab 1 · UC curation (50 min) · `labs/01_uc_curation/01_lab`
**Goal:** decide what the agent may see, make it obvious in metadata, write a context contract.
**Facilitation**
- Step 1 (inventory) is the discussion: push on *which two tables disagree about SAIDI, and why* (`derived_outage_rollup_v1` averages minutes per event instead of weighting by customers).
- Learners have **read-only** access to `ce_shared`, so they curate through **views in their own schema**. This is deliberate: the view is the boundary.
- **Syntax trap:** column comments on a view use `COMMENT ON COLUMN v.c IS '…'`. `ALTER VIEW … ALTER COLUMN … COMMENT` does not exist.
- The checks fail until all six authoritative views have 40+ character descriptions *and* the `ce_certification` tag.
- Stretch (pairs): context engineer vs risk reviewer; the reviewer must find one remaining path for PII or a stale source.

**Debrief:** which single metadata change most improved what an agent could *safely* retrieve? Where would a larger model have helped? (Nowhere.)
**Exam link:** Domain 3, *constrain the agent's retrieval space to authoritative sources before deployment*.

### 5.5 Lab 2 · Genie tuning (45 min) · `labs/02_genie/02_lab`
**Goal:** fix a space with the *smallest correct control* and prove it with a test set.

| Genie control | Use for |
|---|---|
| General instructions | Business vocabulary, definitions, defaults |
| Sample questions | Representative phrasing, discoverability |
| Trusted/example SQL | Validated query patterns for recurring questions |
| SQL expressions (filters, measures) | Reusable calculation logic |

**What the lab actually shows (tested):** a tables-only space scored **4/6**. The two failures were *definitions the data cannot reveal*: the SAIDI denominator (1,000,000 customers served) and that "open" work orders means `open` **and** `in_progress`. Four sentences of instructions plus one measure → **6/6**.

**Facilitation**
- Do not tell learners the answer. Ask, for each FAIL: "What did Genie assume that the business does not?"
- Stress the honest framing: **Genie handles inferable semantics well; you supply the rest.** Do not oversell the failure.
- Change one control at a time and re-score.
- API notes (illustrative, **VERIFY**): `data_sources.tables` must be sorted by identifier; ids are 32-char hex.
- **Terminology VERIFY:** the exam says "trusted SQL assets"; the API field that round-tripped was `example_question_sqls`. Confirm in the UI that these are the same control before stating it.

**Exam link (Domain 2):** correct tables, descriptions and SQL but misread business terms → *general instructions that define the vocabulary*, not more trusted SQL, more sample questions, or a bigger model.

### 5.6 System prompt and few-shot selection (15 min, Domain 2)
- A production prompt states: role and boundary, authoritative sources and precedence, allowed/forbidden actions, tool-use conditions, output contract, uncertainty/escalation behaviour, security constraints.
- **Few-shot by marginal value under a token budget.** Include an example only if it covers an untested tool path, demonstrates a required output structure, resolves an ambiguous request, or shows an important refusal. Exclude redundant, stale or easily inferred examples.
- **Prompt experiment rule:** the longest prompt is not the winner. Ask which element drove the gain, whether it is consistent across cases, and whether a smaller change gives the same result.
- *Exercise:* give three candidate few-shot examples and a 300-token budget. Learners justify keep/drop for each.

### 5.7 Debrief and exam practice (20 min)
Run 2 to 3 scenario questions using the four-step method:
1. **Requirement.** What must improve?
2. **Evidence.** What in the trace proves the root cause?
3. **Constraint.** What must not change?
4. **Minimal fix.** What is the smallest governed change?

Point learners to the official sample questions in the exam guide rather than reproducing them. Write fresh questions for in-room use (`assessment/`).

---

## 6. Session 2 · Retrieval, memory, tools, compaction

### 6.1 Retrieval design (25 min)
**Governed RAG pipeline:** curate authoritative sources → parse and chunk with stable ids and metadata → embed and index → retrieve → filter/rerank → inject only the strongest evidence → generate a grounded answer → trace and evaluate.

**Pre-inference vs just-in-time retrieval**
| | Pre-inference | Just-in-time (agentic) |
|---|---|---|
| When | Before generation | During reasoning, via tool calls |
| Good for | Small, predictable evidence | Needs that depend on intermediate results |
| Risk | Speculative loading wastes context | Needs reliable tool choice and control |

**Chunking: choose from structure and query type, never one universal size**
| Situation | Start with |
|---|---|
| Stable headings | Structure-aware chunks |
| Mixed-length, weakly structured text | Recursive splitter, ~512 to 1,024 tokens, 10 to 15% overlap (*the exam answer for that scenario, not a constant*) |
| Tables/records | Row/entity-aware chunks with schema context |
| Narrow lookups | Smaller chunks |
| Broad synthesis | Larger or parent-child chunks |

**Freshness (a favourite exam item)**
- Delta Sync + **triggered**: when scheduled refresh is enough. *Sync after ingestion.*
- Delta Sync + **continuous**: only when lower latency justifies cost.
- **Direct access**: when the application owns upserts/deletes.
- Stale triggered index after a nightly refresh → **sync after ingestion**, not rebuild, not continuous.

**Semantic vs structured:** meaning/similarity → semantic. Exact ids, ranges, statuses, joins, aggregations → structured. Hybrid (semantic discovery then structured verification) is common.

**Retrieval diagnosis order:** authority and permissions → freshness → metadata → query/filters → chunking → embeddings → candidates/reranking → injection → evaluation coverage.

### 6.2 Lab 3 · AI Search (55 min) · `labs/03_ai_search/03_lab`
**Facilitation**
- Package/client names (**VERIFY**): `pip install databricks-ai-search` (0.81 tested), `from databricks.ai_search.client import AISearchClient` (`VectorSearchClient` is an alias). The old `databricks.vector_search` namespace is *not* installed by it.
- Each learner needs `%pip install` at the top of the notebook (the base environment ships none).
- **The chunking finding (use it):** heading-based splitting puts the *witness requirement* (under "Conditions") in a different chunk from the isolation *steps*. A query about the steps retrieves them without the safety condition. Only the `merged` strategy keeps both together (12 chunks, versus 51 for sentence splitting). Ask learners to find this themselves in Step 7.
- **Filters:** `{"status": "current", "region_code": [region, "ALL"]}`. A list means IN.
- **Stale index:** the lab updates the source table, shows the index is stale, then asks which of four fixes is minimal. Make them write why the other three are wrong *for a nightly requirement*.
- Slow step: index creation. Pre-create or run it during the preceding talk.

**Exam links:** Domain 3 (pipeline, chunking, AI Search diagnosis), Domain 4 (semantic vs structured).

### 6.3 Memory architecture (30 min)
| Memory | Lifetime | Example | Store |
|---|---|---|---|
| Current-turn context | One inference | User question + tool result | Prompt |
| Working memory | Current task | Plan, unresolved items | Scratchpad / task state |
| Session memory | Conversation | Recent turns, summary | Context + checkpoint |
| Long-term | Across sessions | Preferences, durable facts | Lakebase |
| Episodic | Prior events | What happened in a previous work package | Durable store with time/entity metadata |
| Semantic | Stable knowledge | Concepts, profiles | Structured query or semantic retrieval |
| Procedural | Standing how-to | Skills, runbooks | Files/skills (loaded on demand) |

**Rules to repeat**
1. Use the **nearest valid source**. Do not fetch long-term memory if the answer is already in the session.
2. Do not rely on session history for what must survive sessions.
3. Scratchpad only for state that is **temporary, small, local, and safe to lose.** Otherwise durable, governed state.
4. **Resolve user intent before retrieval**, or a good retriever fetches context for the wrong task.
5. Over-retrieval pollutes context; under-retrieval misses history. Tune top-k, filters, recency, authority, dedupe.

**Memory and retrieval as an attack surface (15-min demo, Lab 3b).** Anything persisted or retrieved and later injected into a prompt can poison the context. Lab 5 stores the preference as an *enumerated* value for this reason; ask the room what a free-text preference would allow. Then run the **Lab 3b demo** (`labs/solutions/03b_injection_solution`; the full lab is self-paced or take-home): one honest source, three hostile documents (an obvious injection, a stealthy directive, and a *poisoned fact* with no instruction in it), four defences, measured.

*What we measured (Claude Haiku 5.5 via the gateway, 5 trials per cell, one question; report your own numbers):*

| Attack | No defence | Delimit as data | + keyword scan | + **provenance gate** |
|---|---|---|---|---|
| Obvious injection | clean 0.8 | clean 1.0 | clean 1.0 | clean 1.0 |
| Stealth directive | **clean 0.0** | **clean 0.0** | **clean 0.0** | **clean 1.0** |
| Poisoned fact | **clean 0.0** | **clean 0.0** | **clean 0.0** | **clean 1.0** |

*Teaching points (all from the measurements, and they surprised us):*
1. **The model rarely obeyed** (1 compromised answer in 60 trials, even with no defence). Do not tell the room "models follow injected instructions": this one mostly did not.
2. **The harm is contamination, not obedience.** The hostile content surfaced in the answer and turned a clear safety rule into "the evidence conflicts, it depends on the date" (15/15 for the poisoned fact without a provenance gate). For a field crew that is a clash induced by an unapproved source.
3. **Prompt-level defences did not fix it.** Declaring the evidence to be untrusted data, and scanning for trigger phrases, left the stealth and poisoned-fact answers contaminated every time. The scanner correctly quarantined only the *obvious* payload; the poisoned fact contains no instruction to detect.
4. **Only controlling what may enter context worked:** a provenance gate on `origin` (an ingestion-time, governed metadata field) gave clean answers 15/15. This is the course's theme again: governance beats instruction.

*Limits to state:* one model, small samples, and the "hostile content in answer" metric is a regex that over-counts (it also flags an answer that mentions the notice and then rejects it). Have learners read the printed answers.

### 6.4 Lab 4 · Lakebase memory (45 min) · `labs/04_lakebase_memory/04_lab`
**Facilitation**
- The headline moment: learners throw away the pool, checkpointer and graph ("simulated restart"), rebuild from scratch, resume with the same thread id, and the earlier nodes **do not re-run** (the lab counts executions).
- Pattern (**VERIFY**): `AsyncPostgresSaver(pool)`, `await checkpointer.setup()`, `workflow.compile(checkpointer=checkpointer)`. The pool needs `autocommit=True`, `prepare_threshold=0`, `row_factory=dict_row`.
- Auth: a short-lived (1 h) OAuth credential used as the Postgres password with `user=<email>`; never a stored password.
- Idempotency: the side effect uses `INSERT … ON CONFLICT DO NOTHING`, so a retry cannot duplicate it.
- **Biggest risk: per-learner Postgres roles.** Tested only as the project owner. Create and test roles for a non-admin before the session (§10).

**Exam link (Domain 4):** async LangGraph on Lakebase → `AsyncPostgresSaver` + awaited `setup()` + `compile(checkpointer=…)`.

### 6.5 Tool design, MCP, progressive disclosure, Agent Skills (25 min)
Good tools have: a distinct action-oriented name; a description that says when to use and **when not to**; narrow responsibility; typed parameters; compact result schema; predictable errors; least-privilege access; explicit side effects/idempotency.

**Progressive disclosure:** capability summaries → intent match → load *one* best-fit schema → execute → return only next-step fields → clear raw output once durable facts are extracted. Do not load all schemas and rank afterwards: the token and confusion cost is already paid.

**Exercise.** Four near-identical tools (`fetch_order_status`, `get_order_status`, `retrieve_order_info`, `lookup_order_details`). Have learners consolidate. *Adapt to GridWorks:* `get_work_order`, `fetch_work_order`, `lookup_work_order_details`, `work_order_info`.

**Agent Skills (Domain 5):** move rarely invoked, specialised instructions out of the always-on prompt. Keep frequent safety and core-routing rules in the always-on layer.

### 6.6 Compaction and trimming (20 min)
| Technique | Best when | Risk |
|---|---|---|
| Hard trimming | A simple removal rule applies | Deletes subtle dependencies |
| Sliding window | Recent turns dominate | Loses early constraints/decisions |
| Structured compaction | Long tasks with durable facts and dependencies | A poor summary silently drops state |
| Externalised state | Facts fit durable records | Needs retrieval discipline |

A compaction summary must preserve: goal and status; **user constraints, exclusions, preferences**; decisions and the rationale needed later; authoritative facts with provenance ids; completed actions and material results; unresolved work, dependencies, errors, retries; the next action.

**Never preserve hidden chain-of-thought.** Keep decisions and concise rationale. (The Lab 6 code strips `reasoning` blocks for exactly this reason.)
**Recall before precision:** first make sure every task-critical category survives, then remove duplication and verbose output.
**Exam pattern:** later recommendations contradict earlier decisions → the summary dropped the user's constraints; fix it by retaining a **deduplicated list of constraints, exclusions and preferences**, not by appending every message or chain-of-thought.

---

## 7. Session 3 · Multi-agent, runtime, apps, evaluation

### 7.1 Multi-agent and long-horizon design (20 min)
**Bounded handoff packet:** subtask and success criteria; global constraints; authoritative source references; prior decisions; input/output schema; dependency and freshness markers; a *compressed* coordinator summary when needed.
**Sub-agent output contract:** result, confidence, source ids, assumptions, blockers, a small structured payload. **Not** the full trace.

| Task structure | Strategy |
|---|---|
| Independent parallel subtasks | Parallel sub-agents + compact aggregation |
| Sequential dependencies | Checkpointed workflow |
| Repeated plan/act/observe | Iterative agent with compaction + durable state |
| Human approval | Persisted interrupt/resume |
| Large synthesis | Hierarchical decomposition with source-aware summaries |

**Boundary trade-off:** too many agents → repeated handoff compression and duplicated retrieval; too few → oversized context and tool overload. Place a boundary where there is a distinct tool/data domain, independent evaluation, and a compact contract.

> **Exam note (official sample Q10).** The stated objective says sub-agents got task messages without traces, but the scenario evidence and keyed answer point to a **stale AI Search index** after a Delta update (fix: sync the index). Teach: *evidence beats the objective text*, and check for a revised guide before exam day.

### 7.2 Unity AI Gateway (25 min)
Position it as **runtime governance and a control plane**, not a prompt layer. Per the public docs (updated Oct 2026): control access to model services, MCP servers, tools and agents with Unity Catalog privileges; rate limits and budgets; traffic splitting and fallbacks; **service-policy guardrails**; usage and cost in system tables; request/response logging to Delta.
- Models are queried as fully qualified **model services** (`system.ai.<name>`). In Lab 5/6 the model name is configuration.
- The Python client routes through the gateway with `DatabricksOpenAI(use_ai_gateway=True)` (**VERIFY**); never place provider keys in notebooks or app code.
- **Per-feature GA/preview status is not stated on the docs landing page. VERIFY each feature before claiming GA.**
- Legacy: endpoint-attached "AI Gateway" material should be labelled *legacy*.
- *Live demo idea:* show the model services list, the usage system tables, and a service policy attached to a model service. Only show what you have tested in your workspace.

### 7.3 Lab 5 · The App (50 min) · `labs/05_app/05_lab.md`
**Setup:** deployed by the facilitator (see `app/README.md`). Learners use the shared URL; the stretch part needs their own app name.
**Facilitation**
- Start at the identity banner. The key sentence on screen: **"Runs as: app service principal."** Retrieval and the model call do not run as the user. The user's identity matters for audit and approvals.
- Part 2 is the money moment: run the isolation question with governance ON then OFF and compare the "How this context was built" panel. Governed context was ~42% smaller (1,131 vs 1,937 characters) and the ungoverned run let a superseded and a wrong-region procedure reach the model.
- Part 4: the unique pending-request index makes a double click idempotent. The server returns 409 on a second decision. The *button* is not the control; the server is.
- **Honest limits to state:** the `aiSearch` plugin is **beta**; the UI was verified through its API but has not been visually reviewed; only one identity was tested; the same person can approve their own request (demo only).

**Exam links:** Domain 3 (constrain retrieval space), Domain 4 (nearest valid memory), Domain 5 (approval and tool design).

### 7.4 Lab 6 · MLflow evaluation (55 min) · `labs/06_mlflow_eval/06_lab`
**The evaluation loop (say it before the lab):** define the task and failure modes → representative dataset → instrument traces → choose scorers → baseline → change **one** lever → compare → **inspect failing traces** → promote only with evidence → monitor production samples.

**Tested result (8 cases, 4 configs, `claude-haiku-5-5`)**
| Config | recall | correct | cited | **authority** | mean | **worst** |
|---|---|---|---|---|---|---|
| A baseline (ungoverned) | 1.0 | 1.0 | 1.0 | **0.0** | 0.75 | **0.0** |
| B governed | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| C governed, k=2 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| D governed + strict | 1.0 | 0.88 | 0.88 | 1.0 | 0.94 | 0.88 |

**Teaching points**
1. The baseline's **answers were all correct** while it was fed superseded/draft/wrong-region chunks on almost every call. Only a *context-level* scorer (`authority_safe`) exposed it. Output-only evaluation hides contamination.
2. Selection rule, stated **before** reading the table: every metric ≥ threshold, then the cheapest context. Never the highest mean or one impressive metric (exam: parallel-coordinates chart; not mean, not spread).
3. **Read failing traces before trusting a metric.** An earlier version of `answer_correct` scored a *correct* refusal as wrong because of a brittle keyword list (0.88). The trace showed it. Tell this story; it is the best demonstration of loop step 8.

**Integration traps (tell learners up front)**
- Some model services reject `temperature`.
- `message.content` can be a **list of blocks** (a `reasoning` block, then `text`); extract only `text`.
- `expectations` values must not be `None`; omit the key.
- MLflow **silently drops a metric** if a scorer errors on any row. Assert every metric is present.
- Use serverless environment 4; the evaluation run took about 3 minutes in testing.

### 7.5 Capstone: design review (30 min) · `assessment/`
Teams present a one-page design for a *different* industry using the swap guide (§12). Required artefacts:
1. Business problem: user, decision, value, risk
2. Context inventory: element, source, authority, lifetime, token/cost impact
3. Databricks architecture
4. Governance design: permissions, PII, authoritative sources, freshness, audit, approval gates
5. Context policy: default / just-in-time / persistent / compacted / discarded
6. Tool contract: name, description, inputs, output schema, permissions, side effects
7. Evaluation plan: dataset, scorers, **acceptance thresholds incl. a context-level metric**, regression, monitoring
8. Certification mapping

**Rubric:** business alignment · context quality · Databricks fit (chosen by job) · governance · reliability · evaluation · delivery · partner repeatability.

### 7.6 Exam readiness and action plan (20 min)
See §9.

---

## 8. Partner positioning and ANZ considerations

**Why partners should care**
- Repeatable method: the five questions, the context contract, the evaluation loop.
- Reuse: the same app skeleton, labs and scorers swap across industries.
- Differentiation: governed context and context-level evaluation are what separate a demo from a deliverable.

**ANZ considerations (not legal advice; confirm with the client's compliance team)**
- **Data residency and regional availability.** The course workspace is in Sydney (`ap-southeast-2`). **VERIFY** model-service availability by region.
- **Privacy.** Australian Privacy Act 1988 and the Australian Privacy Principles; New Zealand Privacy Act 2020. Technician/customer PII must not reach prompts (Lab 1).
- **Financial services.** APRA CPS 230 (operational risk management) and CPS 234 (information security): governed access, logging and an auditable approval trail map to these.
- **Critical infrastructure.** For utilities, safety procedures must be authoritative and current: superseded or draft guidance reaching a field crew is a safety risk, not a quality blemish.
- Treat roadmap/preview statements (including Genie Ontology) as positioning inputs, not commitments.

---

## 9. Exam alignment

Official blueprint (*Databricks Certified Context Engineer Associate*, version available from 29 July 2026; **VERIFY** the live guide, a newer August 2026 PDF may exist).

| # | Domain | Weight | Where it is taught | Hands-on evidence |
|---|---|---:|---|---|
| 1 | Foundations of Context Engineering | 16% | §5.2, §5.3 | Trace diagnosis, product map |
| 2 | System Prompt and Instruction Design | 9% | §5.5, §5.6 | Lab 2 |
| 3 | Knowledge Retrieval and Genie Configuration | 20% | §5.4, §5.5, §6.1, §6.2 | Labs 1, 2, 3, 5 |
| 4 | Memory Architecture with Lakebase and MLflow | 18% | §6.3, §6.4, §7.4 | Labs 4, 5, 6 |
| 5 | Tool Design, MCP, and Agent Context | 13% | §6.5 | Tool refactor, Lab 5 |
| 6 | Context Compression and Compaction | 11% | §6.6 | Trace surgery |
| 7 | Multi-Agent and Long-Horizon Task Design | 13% | §7.1 | Boundary exercise, capstone |

**Coverage gaps to be honest about:** Agent Skills, MCP progressive disclosure, compaction and multi-agent design are taught as discussion and exercises, not full labs. Recommend an optional follow-up lab if the budget allows.

**Exam facts (from the official guide; no passing score is published, never state one):** ~45 scored multiple-choice/multiple-selection questions, 90 minutes, USD 200, proctored, no prerequisite (about 6 months' hands-on recommended), valid 2 years.

**Exam technique:** requirement → evidence → constraint → minimal fix.
**Common distractors:** a larger model/window without fixing relevance · continuous sync when triggered is enough · more tools/documents/examples as an automatic fix · fine-tuning for a metadata/retrieval/prompt problem · destructive rebuilds · choosing one metric · preserving raw traces or hidden reasoning.

**Study plan (7 days):** D1 blueprint + failure modes · D2 retrieval + Genie · D3 memory + MLflow · D4 tools + MCP · D5 compaction + multi-agent · D6 official samples under time · D7 review misses only.

---

## 10. Known risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| Environment-2 install hang | High if not configured | Enforce serverless environment 4; pin versions |
| Per-learner Lakebase roles fail (known failure point) | Medium (verified for one principal) | Follow the runbook: valid `role_id` (must start with a letter), `GRANT CREATE ON DATABASE`. Fallback: Lab 4 skip-ahead run by the facilitator; show the restart on screen |
| Index creation slow | Medium | Pre-created reference index; learners create theirs during talk time |
| Learner cannot reach model service | Medium | Facilitator-run Lab 6 results; use the MLflow experiment from rehearsal |
| App `aiSearch` plugin (beta) changes | Medium | Pin the AppKit version at scaffold time; keep the recorded run |
| Grants fail for a non-admin | Low–medium (verified for one principal) | Runbook §1. Most likely miss: the **workspace entitlements**, which produce *'API disabled for users without …'* |
| Two learners map to the same schema name | Medium for mixed-domain cohorts | `02_grants` refuses to run on a collision; rename or split |
| Cannot clean up a learner's Postgres schema | Certain | The project owner cannot drop another role's schema: have the learner drop it, or use a superuser (runbook §4) |
| Session 3 overruns | High | Move capstone to take-home; extended 4 h Session 3 |
| Preview feature unavailable | Medium | Prepared screenshots; label as preview |
| Injection demo shows 'nothing happens' on your model | Medium | That is a valid finding: pivot to the contamination metric and the provenance gate (§6.3). Do not stage a failure |

---

## 11. Integration traps found while building (share with learners)

| Where | Trap | Fix |
|---|---|---|
| Serverless | Environment 2 hangs on `mlflow` 3.x; ships `databricks-sdk 0.40.0` | Use environment 4 and `%pip install` pinned packages |
| Lab 1 | `ALTER VIEW … ALTER COLUMN … COMMENT` is invalid | `COMMENT ON COLUMN v.c IS '…'` |
| Lab 2 | Genie space serialization needs tables **sorted** and 32-char hex ids | Sort identifiers; zero-padded hex ids |
| Lab 3 | Heading-only chunking separates a rule from its condition | Merge small sections |
| Lab 4 | Pool needs `autocommit`, `prepare_threshold=0`, `dict_row` | Copy the pool kwargs from the lab |
| Lab 6 | Model rejects `temperature`; content may be a list with a reasoning block; `None` expectations; metrics dropped silently | See §7.4 |
| Lab 5 | App needs the schema created by its **service principal** | Deploy before local development against Lakebase |
| Scaffolding | `databricks apps init` defaults to pnpm | `--package-manager npm` |

---

## 12. Swapping the scenario

The concepts do not change; the data, vocabulary and permissions do.

| Industry | Authoritative structured data | Document corpus (with superseded/draft/regional variants) | Approval-gated action |
|---|---|---|---|
| **Banking** | Positions, limits, KRIs | Policies, procedures, regulatory guidance | Limit-exception request |
| **Retail** | Orders, stock, promotions | Returns policy, supplier terms | Price override |
| **Public sector** | Cases, service levels | Legislation, operating procedures | Eligibility override |
| **Telco** | Network incidents, SLAs | Runbooks, change records | Change approval |
| **Healthcare** | De-identified activity, rosters | Clinical guidelines (versioned) | Escalation order |

Keep these three properties in any swap: a *definition the data cannot reveal* (Lab 2), a *superseded or draft document plus a regional variant* (Lab 3), and an *action that needs a human* (Lab 4/5).

---

## 13. One-page partner checklist (hand out)

**Context design**
- [ ] What must the agent know? What must it never see?
- [ ] What is authoritative, permitted and fresh enough?
- [ ] Prompt, tool or durable state? What can be dropped after the next decision?

**Retrieval**
- [ ] Sources permissioned and certified; chunk ids, effective dates, authority present?
- [ ] Filters applied *in the index*, not in the prompt?
- [ ] Semantic, structured or hybrid? Index fresh enough for the requirement?

**Tools**
- [ ] Distinct name; says when *not* to use; typed inputs; compact output?
- [ ] Progressive disclosure; side effects idempotent and approval-gated?

**Memory and long horizon**
- [ ] What must survive a restart? A session boundary?
- [ ] Is stored memory constrained so it cannot inject instructions?
- [ ] Does compaction keep constraints, decisions, evidence, dependencies, next action?

**Production**
- [ ] Runtime model/tool access governed and logged?
- [ ] Which identity runs each call, and is it disclosed to the user?
- [ ] Is there a *context-level* metric, a threshold chosen in advance, and a regression alarm?

---

## 14. Source assets
- Databricks Certified Context Engineer Associate: Exam Guide (public PDF) and certification page: facts and weights.
- Databricks blog, *Introducing Genie One, Genie Agents, and Genie Ontology* (16 June 2026): GA/preview status.
- AI governance with Unity Gateway (Databricks docs, updated Oct 2026).
- AppKit documentation (`npx @databricks/appkit docs`), AI Search plugin (beta).
- Lab 3b is original to this course; the documents in it are fictional.
- Product availability notes rely on public sources only (see `docs/00_fact_sheet.md` §5 and §7).

## 15. Delivery caveats
This is a partner-enablement design, not an official Databricks certification course. Exam guides, documentation, SDKs and product names change; refresh before every cohort. Preview and roadmap statements are not commitments. Code is deliberately small and illustrative: add authentication, retries, structured logging, resource declarations, secret handling, error handling and tests for production.

### What is not yet built or verified
- Decks are built (`slides/`: 3 HTML decks, 48 slides, speaker notes on N). Not yet tested on a venue projector.
- The assessment pack exists (`assessment/`: parallel pre/post forms, answer key, course-specific questions, capstone rubric). The quiz has **not** been piloted with real learners, so its difficulty is unvalidated.
- Verified since first draft: Labs 1 to 4 on environment 4; the Lab 5 UI in a real browser (5 defects fixed and redeployed); Labs 1 and 4 as a non-admin learner principal with a refusal test (8 of 8). See `docs/00_fact_sheet.md` §14 to §16.
- Still unverified: a real **human** learner (user-type Lakebase roles, OAuth sign-in), **15 concurrent** learners, group-based grants, Labs 3/6 as a non-admin, on-behalf-of-user mode in the app.
