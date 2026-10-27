# Capstone: design review rubric and template

**Task.** In teams of 3 to 4, design a governed context-engineered assistant for a **different industry** from GridWorks (see the swap table in the facilitator guide §12). Present in 5 minutes; 3 minutes of questions from a "risk reviewer" team.

## One-page design template (teams fill this in)

| # | Artefact | Your answer |
|---|---|---|
| 1 | **Business problem**: user, decision, value, risk if wrong | |
| 2 | **Context inventory**: for every element, its *source*, *authority*, *lifetime*, and token/cost impact | |
| 3 | **Databricks architecture**: which capability does which job (UC, Genie, AI Search, Lakebase, MCP, Gateway, Apps, MLflow) | |
| 4 | **Governance**: permissions, PII, authoritative vs derived sources, freshness, audit, approval gates, **trusted origins** | |
| 5 | **Context policy**: what is default / just-in-time / persistent / compacted / discarded | |
| 6 | **Tool contract**: name, when to use and *not* use, inputs, output schema, permissions, side effects, idempotency | |
| 7 | **Evaluation plan**: dataset (include traps), scorers (**at least one context-level**), acceptance thresholds chosen *in advance*, regression and production monitoring | |
| 8 | **Exam mapping**: which blueprint domain each major decision exercises | |

**Ground rules**
- Use at least one *definition the data cannot reveal*, one *superseded or draft source*, and one *action that needs a human*.
- Name the identity each call runs as (user or service principal) and say why.
- State one thing you chose **not** to build, and why.

## Scoring (0 to 4 per dimension, 32 total)

| Dimension | 0 to 1: weak | 2: adequate | 3: strong | 4: excellent |
|---|---|---|---|---|
| **Business alignment** | Technology-first; no decision or value named | Names the user and decision | Quantifies value and the cost of a wrong answer | Ties thresholds and design choices to the stated risk |
| **Context quality** | "Give it everything"; no lifetimes | Some selection logic | Each element has a source, authority and lifetime; minimal by default | Explicit just-in-time vs default split with token impact |
| **Databricks fit** | Products listed, not mapped to jobs | Mostly correct mapping | Every capability tied to a job-to-be-done; alternatives rejected with a reason | Notes preview/GA status honestly and a fallback |
| **Governance** | Governance is a final checklist | Permissions and PII mentioned | Retrieval space constrained *before* the model; certified sources; freshness stated | Also covers trusted origins, approval gates, audit, and the identity each call runs as |
| **Reliability** | Failure modes unnamed | Names some failure modes | Maps each of the four failure modes to a mitigation | Addresses poisoning via retrieved content and a restart/resume path |
| **Evaluation** | "We will test it" | Metrics listed | Baseline, one-lever-at-a-time changes, multi-metric selection | Context-level scorer, thresholds fixed beforehand, failing traces inspected, production regression alarm |
| **Delivery** | Notebook only | Names an app | Identity, resource bindings, approvals and telemetry addressed | Operating model, cost and ownership, cleanup |
| **Partner repeatability** | One-off | Reusable parts noted | Clear what swaps per client and what stays | Packaged assets, a sizing note, and a client-facing checklist |

**Pass bar:** 20 or more of 32 **and** no dimension scored 0.
**Distinction:** 26 or more **and** Evaluation and Governance each scored 3 or more.

## Reviewer prompts (use these in the Q&A)
1. "Show me one thing the assistant is *not* allowed to see, and where that is enforced." (Expect: in the query/permissions, not the prompt.)
2. "A document from an unapproved source says a safety rule is withdrawn. What happens?" (Expect: provenance gate; not a keyword scanner.)
3. "Which metric would have caught that your answers were right for the wrong reasons?"
4. "What survives a restart, and what happens if the approval is clicked twice?"
5. "Which exam objective does your riskiest decision exercise?"

## Calibration (assessors, 10 minutes before presentations)
Score one sample design together first. Agree what a "3" means for Governance and Evaluation, since those two carry the course's main lessons.
