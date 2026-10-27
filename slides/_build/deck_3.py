from lib import *

def build():
    d = Deck("Context Engineering: Session 3", "Session 3 · Multi-agent, runtime, apps, evaluation", "s3")

    d.title("From design to proof",
            "Multi-agent context, the gateway, the app, and evaluation",
            "ANZ C&amp;SI partner enablement · Session 3 of 3 · 3.5 hours",
            notes="Recap: retrieval, memory, tools, compaction. Today: how agents hand context to each other, how the runtime is governed, how the product surface carries all of it, and how we prove it worked.")

    d.content("Multi-agent design", "Send a bounded packet, not the whole trace",
        two('<h3>Down to a sub-agent</h3><ul><li>Subtask and success criteria</li><li>Global constraints</li><li>Authoritative source references</li><li>Prior decisions and freshness marker</li></ul>',
            '<h3>Back to the coordinator</h3><ul><li>Result and confidence</li><li>Source ids and assumptions</li><li>Blockers</li><li>A small structured payload</li></ul>'),
        notes="Domain 7. Sub-agents need updated context in compact form. The full raw trace blows the window; an isolated task message loses the update. Output contracts keep the orchestrator from saturating.")

    d.content("Matching the strategy", "Match the architecture to the task",
        rows(["Task structure", "Strategy"], [["Independent parallel work", "Parallel sub-agents, compact aggregation"], ["Sequential dependencies", "Checkpointed workflow"], ["Plan, act, observe", "Iterative agent with compaction and durable state"],
              ["Human approval", "Persisted interrupt and resume"], ["Large synthesis", "Hierarchical decomposition with source-aware summaries"]]),
        kind="white",
        notes="Boundary trade-off: too many agents means repeated handoff compression and duplicated retrieval; too few means oversized context and tool overload. Place a boundary at a distinct tool or data domain, independent evaluation, and a compact contract.")

    d.content("Boundaries", "Where you draw the line is a context decision",
        cards([("Too many agents", "Handoffs lose detail", "Repeated compression. Coordination dominates cost."), ("Too few agents", "One window does everything", "Tool overload and attention saturation.")], cols=2)
        + '<p class="note-tag">Exam note: sample question 10 has an objective that does not match its keyed answer. Evidence beats the objective text.</p>',
        notes="Official sample Q10 states a sub-agent trace objective but the scenario evidence and keyed answer point to a stale AI Search index; sync it. Teach: read the evidence. Check for a revised guide before exam day.")

    d.add("ink", "Unity AI Gateway",
          '<span class="eyebrow">Runtime governance</span><h2>The gateway governs the runtime, not the prompt</h2><div class="accent-line"></div>'
          + cards([("Access", "Who can reach what", "Unity Catalog privileges on models, tools and MCP."), ("Traffic", "Limits and fallbacks", "Rate limits, budgets, traffic splitting."),
                   ("Guardrails", "Service policies", "Control requests and responses."), ("Visibility", "Usage and logs", "System tables and request logging.")], cols=4)
          + '<p class="note-tag">Verify GA or preview status per feature before you claim it.</p>',
          "Per the public docs (updated October 2026). Models are fully qualified model services (system.ai.name). No provider keys in notebooks or app code. Per-feature GA and preview status is not stated on the docs landing page; verify each feature. Label older endpoint-attached AI Gateway material as legacy. Only demo what you have tested.")

    d.content("Lab 5 · 50 min · Domains 1, 3, 4, 5", "The product surface is part of the context",
        cards([("Identity", "Who the call runs as", "Shown on screen: the app's service principal."), ("Governance", "A switch you can flip", "See what reaches the model."), ("Memory", "Saved and session choices", "Nearest valid source wins."), ("Approval", "A human in the loop", "Idempotent, enforced by the server.")], cols=4),
        notes="The app is deployed by the facilitator. Start at the identity banner: retrieval and the model call do not run as the user. Part 2 is the money moment. Honest limits: the aiSearch plugin is beta; the UI was verified in a real browser but only with one identity; the same person can approve their own request (demo only).")

    d.stat("Measured in Lab 5", '<div class="stat-col"><span class="big good">−42%</span><span class="sub">Characters of context, governed vs ungoverned</span></div>',
           "Governed context for the same question: 1,131 characters against 1,937. The superseded and wrong-region procedures stayed out.",
           heading="Governance made the context smaller and safer",
           notes="Governed: current plus region-permitted chunks only. Ungoverned: a superseded VIC procedure and the NSW variant reached the model. The answer looked fine either way, which is the point of Lab 6.")

    d.content("Evaluation loop", "Prove it with a loop, not a feeling",
        flow(["Define the task and failure modes", "Build a set with traps", "Instrument traces", "Choose scorers", "Run a baseline", "Change one lever", "Read the failing traces", "Promote on evidence, then monitor"]),
        kind="white",
        notes="Say the loop before the lab. Track correctness, context recall, groundedness, retrieval precision, task success, latency, tokens, cost, safety and variance. Reliability is balanced performance, not the highest single metric or the mean.")

    d.add("dark", "Lab 6",
          '<span class="eyebrow">Lab 6 · 55 min · Domains 2 and 4</span><h2>Compare four context configurations</h2><div class="accent-line"></div>'
          + lab_box("Compare four context configurations on eight questions.",
                    ["Write two scorers", "Run the baseline, change one lever", "Compare every metric", "State your selection rule first"],
                    "You can defend the winner on its worst metric.")
          + tags([("Use serverless environment 4", "lava"), ("About 3 minutes per run", "teal")]),
          "Install mlflow 3.17.2 and databricks-openai 0.18.0 on environment 4 (environment 2 hangs on mlflow 3). Integration traps: some models reject temperature; content can arrive as a list with a reasoning block; None is invalid in expectations; a scorer error silently drops the metric.")

    d.stat("Measured in Lab 6", pair("1.0", "Answers correct", "good", "0.0", "Context kept clean", "bad", sep="but"),
           "Baseline: every answer correct, yet superseded, draft and wrong-region chunks reached the model on almost every call.",
           heading="Right answers, contaminated context",
           notes="Left is answer correctness, right is the authority-safe context score. Output-only evaluation hides contamination. Only the context-level scorer exposed it.")

    d.content("Selection", "Choose on the worst metric, not the average",
        hbars([("A · baseline (mean 0.75)", 0, "hot", "0.00"), ("B · governed (mean 1.00)", 100, "good", "1.00"), ("C · governed, k=2 (mean 1.00)", 100, "good", "1.00"), ("D · governed + strict (mean 0.94)", 88, "", "0.88")])
        + '<p class="caption">Worst single metric per configuration. C wins: every metric clears the threshold with the smallest context.</p>',
        kind="white",
        notes="The baseline's mean of 0.75 hides a 0.0. Selection rule, stated before reading the table: every metric at or above the threshold, then the cheapest context. D shows strictness has a cost: correctness and citations fell to 0.88. Exam: parallel coordinates, not mean, not spread, not the single best metric.")

    d.add("ink", "State the rule first",
          '<span class="eyebrow">Discipline</span><div class="pull-quote">State the selection rule before you read the table.</div>',
          "Tell the story: an earlier version of the correctness scorer marked a correct refusal as wrong, so governed configs scored 0.88. The trace showed the agent had refused correctly. Always read the failing traces before you trust a metric.")

    d.content("Capstone · 30 min", "Design it for another industry",
        cards([("1", "Problem", "User, decision, value, risk"), ("2", "Context inventory", "Source, authority, lifetime"), ("3", "Architecture", "Capability per job"), ("4", "Governance", "Permissions, PII, origins"),
               ("5", "Context policy", "Default, just in time, kept, dropped"), ("6", "Tool contract", "Inputs, outputs, effects"), ("7", "Evaluation", "Include a context-level metric"), ("8", "Exam map", "Domain per decision")], cols=4),
        notes="Teams of 3 to 4 present five minutes, with three minutes of questions from a risk reviewer team. Use the swap table in the facilitator guide. Rubric: 8 dimensions scored 0 to 4; pass is 20 of 32 with no zero. Reviewer prompt: a document from an unapproved source says a safety rule is withdrawn. What happens?")

    d.content("Exam readiness", "Three domains carry 54% of the exam",
        hbars([("Retrieval and Genie", 20, "hot", "20%"), ("Memory, Lakebase, MLflow", 18, "hot", "18%"), ("Foundations", 16, "hot", "16%"), ("Tools and MCP", 13, "", "13%"), ("Multi-agent", 13, "", "13%"), ("Compaction", 11, "", "11%"), ("Prompt and instructions", 9, "", "9%")])
        + '<p class="caption">About 45 questions, 90 minutes, proctored. No published passing score. Check the live exam guide before you book.</p>',
        kind="light",
        notes="Weights are from the official guide for the version available from 29 July 2026; verify the live guide as a newer version may exist. Technique: requirement, evidence, constraint, minimal fix. Distractors: bigger model, continuous sync, more context, fine-tuning for a context problem, destructive rebuild, a single metric, preserving raw traces. This is not an official certification course and does not guarantee a pass.")

    d.closing("Your action plan", ["Redo the capstone and explain each choice aloud", "Take the post-course quiz (Form B)", "Study retrieval, memory and foundations first", "Re-read the official exam guide before booking"],
              "Close on the promise, then the pre and post quiz gain. Hand out the one-page partner checklist from the facilitator guide. Clean up learner schemas and the Lakebase project when the cohort ends.")
    return d
