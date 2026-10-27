from lib import *

def build():
    d = Deck("Context Engineering: Session 1", "Session 1 · Foundations, governance, Genie", "s1")

    d.title("Context Engineering on Databricks",
            "Foundations, governance and Genie",
            "ANZ C&amp;SI partner enablement · Session 1 of 3 · 3.5 hours",
            notes="Welcome. Set the contract for the day: this is a systems course, not prompt writing. Ask the room to keep one real agent failure in mind; we sort it by failure mode later in this session.")

    d.add("ink", "The model is rarely the problem",
          '<span class="eyebrow">Why we are here</span><h1>The model is rarely the problem. <span class="hl">The information around it is.</span></h1>'
          '<div class="accent-line wide"></div><p class="lead">Reliability comes from what the agent sees, when it sees it, and where it came from.</p>',
          "Open with the claim, then ask for a show of hands: who has fixed an agent by changing the model, and who fixed it by changing what the agent saw? Collect two or three failures on a board. Do not solve them yet.")

    d.content("The course promise", "One promise, five questions",
        cards([("01", "Need", "What does the agent actually need?"), ("02", "Timing", "Before inference, just in time, or later?"),
               ("03", "Authority", "Which source is authoritative, permitted, fresh?"), ("04", "Efficiency", "How do we cut tokens and ambiguity?"),
               ("05", "Proof", "Which trace or metric shows it helped?")], cols=5),
        lead="Give the agent the right context, at the right time, in the smallest useful form, from governed sources, and prove the choice with evaluation.",
        notes="This is the spine for all three sessions. Every design decision gets the same five questions. House rule: nobody says 'use a bigger model' as a first answer unless a trace shows capacity, not context quality, is the limit.")

    d.content("Definition", "Context is everything the model sees",
        cards([("You write", "Instructions and examples", "System prompt, policies, few-shot examples, output contract."),
               ("Retrieved", "Evidence and memory", "Documents, rows, SQL results, long-term memory, summaries."),
               ("From the loop", "State and tools", "Conversation, tool schemas and outputs, other agents' messages.")], cols=3),
        lead="Prompt engineering shapes instructions. Context engineering manages the whole information environment.",
        kind="white",
        notes="Walk the nine elements by category. Stress that tool schemas and tool outputs are context too: that is where many token budgets go. Prompt engineering is one input; selection, timing, authority, persistence and evaluation are the rest.")

    d.content("Failure modes", "Four ways context fails",
        cards([("Poisoning", "A false fact becomes a premise", "Fix: remove or block the source."),
               ("Distraction", "Valid context buries the task", "Fix: scope, clear, or compact."),
               ("Confusion", "The wrong source or tool is used", "Fix: fewer candidates, sharper metadata."),
               ("Clash", "Context elements disagree", "Fix: set precedence and one source of truth.")], cols=4),
        notes="Teach each with its trace signal. Also name context rot and context exhaustion: past a point more tokens hurt, non-uniformly, and attention degrades before the hard limit. Exam note: irrelevant prior-session content that gets used in a new answer is confusion, not poisoning.")

    d.add("dark", "Trace diagnosis exercise",
          '<span class="eyebrow">Exercise · 15 min · groups of 3</span><h2>Name it. Cite the evidence. Propose the smallest fix.</h2><div class="accent-line"></div>'
          + cards([("Trace A", "A stale address", "Pulled from long-term memory, again and again."),
                   ("Trace B", "100 pages of logs", "Valid, but the latest constraint is ignored."),
                   ("Trace C", "Last week's contract", "A prior session leaks into today's answer."),
                   ("Trace D", "Two policies", "Equally authoritative, different escalation rules.")], cols=4),
          "Answers: A poisoning, B distraction, C confusion, D clash. Groups should name the failure, cite the evidence, and give the smallest fix. Reject 'use a larger model'. Expect an argument on C; that is the exam nuance, let them have it.")

    d.content("Attention budget", "Attention runs out before the window does",
        two('<h3>What we know</h3><ul><li>Quality can degrade well before the limit.</li><li>More tokens can hurt, unevenly.</li><li>Compaction beats a bigger window.</li></ul>',
            '<h3>Match the reasoning mode</h3>' + rows(["Mode", "Use for"], [["<b>Standard</b>", "Routine decisions, tool use"], ["<b>Extended</b>", "Only where measured gain pays for the tokens"], ["<b>Reduced</b>", "Routing, classification, extraction"]])),
        kind="light",
        notes="Domain 1 easy points. Choose reasoning mode by task and token budget. A router that must answer in 300 ms does not want extended thinking. Tie it to context pressure: reasoning tokens consume the same budget.")

    d.content("The Databricks stack", "Pick the product by the job",
        rows(["Job to be done", "Capability"], [
            ["Govern data, tools, PII", "<b>Unity Catalog</b>"], ["Retrieve by meaning", "<b>AI Search</b> (formerly Vector Search)"],
            ["Ask governed data", "<b>Genie</b>"], ["Remember across sessions", "<b>Lakebase</b>"], ["Connect tools", "<b>MCP</b>"],
            ["Load rare instructions", "<b>Agent Skills</b>"], ["Govern model and tool traffic", "<b>Unity AI Gateway</b>"],
            ["Ship securely", "<b>Databricks Apps</b>"], ["Prove it works", "<b>MLflow 3</b>"]])
        + '<p class="note-tag">Genie Ontology is a preview capability. Treat roadmap statements as positioning, not commitments.</p>',
        kind="white",
        notes="Teach by job, not product tour. Architecture prompt: where should information live if it must survive a restart, be shared by workers, be auditable and not use prompt tokens? Answer: durable governed state. Genie One and Genie Agents are generally available per the public 16 June 2026 blog; Genie Ontology is a preview capability. Verify current status before you say more.")

    d.add("dark", "Lab 1",
          '<span class="eyebrow">Lab 1 · 50 min · Domain 3</span><h2>Curate the context the agent may use</h2><div class="accent-line"></div>'
          + lab_box("Decide what the agent may see, and write it down.",
                    ["Classify the 11 assets", "Describe and tag the six certified ones", "Build a PII-free view", "Write the context contract"],
                    "Every check prints PASS.")
          + tags([("Unity Catalog", "teal"), ("Views are the boundary", "lava")]),
          "Learners curate through views in their own schema because they have read-only access to the shared data. Push on: which two tables disagree about SAIDI and why. Syntax trap: column comments on a view use COMMENT ON COLUMN. Skip-ahead: labs/solutions/01_uc_curation_solution.")

    d.add("ink", "Governance is context construction",
          '<span class="eyebrow">Governance is context construction</span><div class="pull-quote">A technically relevant result can still be unauthorised, stale, or unsafe.</div>',
          "Land the idea: governance is not a final checklist. Metadata, certification, lineage, permissions and source scope decide what the agent retrieves and trusts. Ask: where would a larger model have helped in Lab 1? Nowhere.")

    d.content("Lab 2 · 45 min · Domains 2 and 3", "Tune Genie with the smallest correct control",
        cards([("Instructions", "Vocabulary and definitions", "What words and numbers mean."), ("Sample questions", "User phrasing", "Discoverability."),
               ("Example SQL", "Validated queries", "Recurring questions."), ("SQL expressions", "Reusable logic", "Filters and measures.")], cols=4)
        + tags([("Score six questions", "teal"), ("Change one control at a time", "lava")]),
        lead="Start with tables only. Score the test set. Fix one failure at a time.",
        notes="Do not tell the answer. For each FAIL ask: what did Genie assume that the business does not? Be honest: Genie handles inferable semantics well; you supply the rest. API notes are illustrative: tables must be sorted by identifier and ids are 32-character hex. Verify that the exam's trusted SQL is the API's example SQL before you say they are the same.")

    d.stat("Measured in the lab", pair("4/6", "Tables only", "bad", "6/6", "Plus 4 sentences and 1 measure", "good"),
           "Four sentences of instructions and one measure. No new tables. No bigger model.", heading="Genie lacked definitions, not data",
           notes="The two failures were definitions the data cannot reveal: the SAIDI denominator (1,000,000 customers served) and that 'open' work orders includes in-progress. This is the Domain 2 lesson: correct tables and SQL but misread terms means general instructions that define the vocabulary.")

    d.content("Domain 2", "Include an example only if it earns its tokens",
        two('<h3>Include when it</h3><ul><li>Covers an untested tool path</li><li>Shows the required output structure</li><li>Resolves an ambiguous request</li><li>Demonstrates a refusal</li></ul>',
            '<h3>Exclude when it is</h3><ul><li>Redundant or near-duplicate</li><li>Stale or low-frequency</li><li>Easy to infer from instructions</li></ul><p class="caption">The longest prompt is not the winner.</p>'),
        kind="white",
        notes="Exercise (5 min): give three candidate examples and a 300-token budget; learners justify keep or drop. For prompt experiments ask which element drove the gain, whether it holds across cases, and whether a smaller change gives the same result.")

    d.content("Exam method", "Requirement, evidence, constraint, minimal fix",
        flow(["What must improve?", "What proves the root cause?", "What must not change?", "Smallest governed change"])
        + hbars([("Foundations", 16, "", "16%"), ("Prompt and instruction design", 9, "", "9%"), ("Retrieval and Genie", 20, "hot", "20%")])
        + '<p class="caption">Today covers 45% of the blueprint.</p>',
        notes="Use the four steps on every scenario question. Point learners to the official sample questions in the exam guide rather than reproducing them. No passing score is published; never state one.")

    d.closing("Before Session 2", ["Classify one real agent failure by mode", "Finish both lab checks, or run the solution notebook", "Bring a question about chunking or memory"],
              "Close on the promise. Confirm everyone has an environment version 4 notebook that runs and a schema of their own. Session 2 starts with retrieval design.")
    return d
