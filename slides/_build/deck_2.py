from lib import *

def build():
    d = Deck("Context Engineering: Session 2", "Session 2 · Retrieval, memory, tools, compaction", "s2")

    d.title("Retrieval, memory and tools",
            "Governed retrieval, durable state, and compaction",
            "ANZ C&amp;SI partner enablement · Session 2 of 3 · 3.5 hours",
            notes="Recap Session 1 in two sentences: context fails four ways, and governance decides what the agent may see. Today is how information gets in, how it persists, and how it is shrunk.")

    d.content("Retrieval design", "Retrieve before generating, or as you go",
        cards([("Pre-inference", "Load a small, predictable set", "Simpler to bound and test. Wastes context if loaded speculatively."),
               ("Just in time", "Fetch as the task unfolds", "Adapts to intermediate results. Needs reliable tool choice.")], cols=2)
        + tags([("Semantic: meaning and similarity", "teal"), ("Structured: ids, ranges, joins", "lava")]),
        lead="Use semantic search to discover and structured queries to verify. Hybrid is common.",
        notes="Domain 3 and 4. Pre-inference retrieval is embedding-based and up front; just-in-time retrieval is tool calls and dynamic queries. Exact predicates (ids, dates, statuses, aggregations) are structured work; fuzzy 'similar to' is semantic.")

    d.content("The pipeline", "Retrieval is a pipeline you govern",
        flow(["Curate authoritative sources", "Chunk with stable ids and metadata", "Embed and index", "Retrieve candidates", "Filter by authority and region", "Inject only the strongest evidence", "Answer with citations", "Trace and evaluate"]),
        kind="white",
        notes="Walk the eight steps. Stress step 5: authority and permission are enforced in the index query, before the model sees anything. Diagnosis order when quality is poor: authority and permissions, freshness, metadata, query and filters, chunking, embeddings, candidates, injection, evaluation coverage.")

    d.content("Chunking", "Choose the split from structure and query type",
        rows(["Situation", "Start with"], [["Stable headings", "Structure-aware chunks"], ["Mixed length, weak structure", "Recursive split, 512 to 1,024 tokens, 10 to 15% overlap*"],
              ["Tables and records", "Row or entity chunks with schema context"], ["Narrow lookups", "Smaller chunks"], ["Broad synthesis", "Larger or parent-child chunks"]])
        + '<p class="note-tag">*The exam answer for that scenario, not a universal constant.</p>',
        notes="Do not present one chunk size as universal. The 512 to 1,024 token and 10 to 15% overlap figures are the keyed answer for the exam's mixed-length wiki scenario.")

    d.stat("Measured in Lab 3", pair("51", "Chunks: sentence splitting", "bad", "12", "Chunks: merged sections", "good"),
           "Chunks per corpus: sentence splitting versus merged sections. Only merged chunks kept the witness rule with its steps.",
           heading="Where you split decides what the agent knows",
           notes="Heading-based splitting puts the witness requirement (under Conditions) in a different chunk from the isolation steps, so a query about the steps retrieves them without the safety condition. Only the merged strategy keeps both. Let learners find this themselves in the stretch step.")

    d.content("Freshness", "A stale index has a minimal fix",
        cards([("Delta Sync · triggered", "Sync after ingestion", "Right when scheduled freshness is enough."), ("Delta Sync · continuous", "Only for low latency", "Justified by a real latency requirement."),
               ("Direct access", "Your app owns upserts", "Use when you manage records, not a Delta source.")], cols=3)
        + '<p class="caption">Stale after a nightly refresh? Sync after ingestion. Do not rebuild. Do not go continuous.</p>',
        notes="A favourite exam item. The lab updates a source row, shows the triggered index is stale, then asks which of four fixes is minimal. Make learners write why the other three are wrong for a nightly requirement.")

    d.add("dark", "Lab 3",
          '<span class="eyebrow">Lab 3 · 55 min · Domains 3 and 4</span><h2>Governed retrieval with AI Search</h2><div class="accent-line"></div>'
          + lab_box("Chunk, index, filter by authority, fix a stale index.",
                    ["Chunk with stable ids", "Create a triggered index", "Add status and region filters", "Fix staleness the minimal way"],
                    "Governed search returns only current, regional documents.")
          + tags([("pip install databricks-ai-search", "teal"), ("Index creation takes minutes", "lava")]),
          "Package and client names are illustrative: databricks-ai-search 0.81, AISearchClient (VectorSearchClient is an alias). Each notebook installs its own pinned packages; the base environment ships none. Pre-create the index or run creation during the talk.")

    d.section(2, "Memory", "Use the nearest valid source.", "Introduce the idea that memory has a lifetime, and that the right store follows from it.")

    d.content("Memory lifetimes", "Every memory has a lifetime and a home",
        rows(["Memory", "Lifetime", "Lives in"], [["Current turn", "One inference", "The prompt"], ["Working", "Current task", "Scratchpad or task state"], ["Session", "One conversation", "Checkpoint"],
              ["Long-term", "Across sessions", "Lakebase"], ["Episodic", "Prior events", "Durable store with time and entity"], ["Procedural", "Standing how-to", "Skills and runbooks"]], three=True),
        kind="white",
        notes="Rules to repeat: use the nearest valid source; do not fetch long-term memory if the answer is already in the session; do not rely on session history for what must survive sessions; resolve user intent before retrieval.")

    d.content("Scratchpad or durable state", "Persist only what must survive",
        cards([("Scratchpad when", "Temporary, small, local", "Safe to lose. Never audited. Dies with the process."),
               ("Durable state when", "It must survive", "A restart, a session boundary, or a second worker. Or it must be auditable.")], cols=2),
        notes="Exam pattern: identify when a Delta or Lakebase-backed state object is required over an in-context scratchpad for a multi-step task. Over-retrieval pollutes context; under-retrieval misses history.")

    d.add("dark", "Lab 4",
          '<span class="eyebrow">Lab 4 · 45 min · Domain 4</span><h2>Survive a restart</h2><div class="accent-line"></div>'
          + lab_box("Checkpoint, pause for approval, resume after a restart.",
                    ["Connect with a short-lived credential", "Build the graph with a checkpointer", "Discard everything, rebuild, resume"],
                    "Earlier steps do not run again.")
          + tags([("AsyncPostgresSaver", "teal"), ("await checkpointer.setup()", "lava")]),
          "Headline moment: learners discard the pool, checkpointer and graph, rebuild from scratch, resume with the same thread id, and the earlier nodes do not re-run. Pin psycopg 3.2.13: the 3.3.x binary wheel aborts at import on serverless environments 3 and 4. Biggest risk: per-learner Postgres roles; follow the provisioning runbook.")

    d.content("Demo · 15 min", "A document can poison context without giving orders",
        cards([("Obvious injection", "Says: ignore previous instructions", "Easy to spot with a scanner."), ("Stealth directive", "Policy-sounding, no markers", "A scanner finds nothing to match."),
               ("Poisoned fact", "A false claim, no instruction", "Looks like an amendment to the rule.")], cols=3),
        lead="All three are marked current, so a status filter lets them through.",
        notes="Lab 3b. One authoritative chunk says a witness is required for 33kV isolations in NSW. Three hostile chunks from an external email origin try to undo that. Ask the room to predict before you show results. Most people over-predict how often the model obeys.")

    d.add("dark", "Only controlling what may enter context worked",
          '<span class="eyebrow">Measured · poisoned fact · 5 trials per row</span><h2>Only controlling what may enter context worked</h2><div class="accent-line"></div>'
          + hbars([("No defence", 0, "hot", "0%"), ("Evidence declared as data", 0, "hot", "0%"), ("Plus keyword scan", 0, "hot", "0%"), ("Plus provenance gate", 100, "good", "100%")])
          + '<p class="caption">Share of clean answers. The model rarely obeyed; the harm was contamination: a clear rule became "the evidence conflicts". One model, small samples. Report your own numbers.</p>',
          "Clean means the answer says a witness is required and does not surface the hostile document as a competing authority. The model was compromised in 1 of 60 trials with no defence; the damage was ambiguity. Delimiting evidence and keyword scanning did not help the stealth or poisoned-fact cases. A provenance gate on an ingestion-time origin field gave clean answers in 15 of 15. The measure is a regex and over-counts; have learners read the printed answers.")

    d.content("Tool design", "A good tool says when not to use it",
        cards([("Name", "Distinct, action-oriented", "Not four ways to say get order."), ("Scope", "One narrow job", "Least-privilege access."), ("Contract", "Typed in, compact out", "Predictable errors."), ("Effects", "Explicit and idempotent", "Safe to retry.")], cols=4),
        notes="Exercise: four near-identical tools. Consolidate them and write use and avoid-use conditions. Adapt to GridWorks: get_work_order, fetch_work_order, lookup_work_order_details, work_order_info. Agent Skills: move rarely used capability instructions out of the always-on prompt; keep safety and core routing in.")

    d.content("Progressive disclosure", "Load one schema, not sixty",
        flow(["Show capability summaries", "Match the user's intent", "Load the best-fit schema only", "Execute", "Return only next-step fields", "Clear raw output once facts are saved"]),
        lead="Do not load every schema and rank afterwards: the token and confusion cost is already paid.", kind="white",
        notes="Exam: staged discovery reduces tokens compared with raw tool dumps. For MCP on Apps, a three-layer discovery, planning and execution server with governed connections and compact responses.")

    d.content("Compaction", "A summary must keep what the task needs",
        two('<h3>Keep</h3><ul><li>Goal and status</li><li>User constraints and exclusions</li><li>Decisions and needed rationale</li><li>Facts with source ids</li><li>Open work and next action</li></ul>',
            '<h3>Drop</h3><ul><li>Duplicate tool payloads</li><li>Verbose logs</li><li>Superseded candidates</li><li><b>Hidden reasoning</b>: never keep it</li></ul>'),
        notes="Recall before precision: first make every task-critical category survive, then remove duplication. Compare trimming, sliding window, structured compaction and externalised state. The Lab 6 code strips reasoning blocks for exactly this reason.")

    d.add("ink", "The exam pattern",
          '<span class="eyebrow">The exam pattern</span><div class="pull-quote">Later recommendations contradict earlier decisions? The summary lost the user\'s constraints.</div>',
          "The fix is a deduplicated list of constraints, exclusions and preferences, not appending every message, every tool output, or the model's reasoning. Run one trace-surgery exercise from your own examples if time allows.")

    d.closing("Before Session 3", ["Finish Labs 3 and 4, or run the solutions", "Write one tool description with an avoid-use line", "Think of an action your agent takes that needs a human"],
              "Session 3 covers multi-agent design, the gateway, the app, and evaluation. Remind everyone to use serverless environment 4.")
    return d
