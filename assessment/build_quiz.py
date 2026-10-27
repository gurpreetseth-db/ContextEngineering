"""Generates the pre/post quiz forms and the answer key from one source of truth.

Each question is written CORRECT-ANSWER-FIRST; options are shuffled with a fixed seed and the key is computed,
so the key can never disagree with the options. All questions are original (not taken or paraphrased from the
official exam samples or from third-party study material).
Run:  python3 assessment/build_quiz.py
"""
import random, pathlib

# (id, domain, stem, [correct, distractor, distractor, distractor], rationale)
FORM_A = [
 ("A1", "1 Foundations",
  "A control-room agent retrieves two procedures for the same task. Both are marked current and approved: one says escalate to the duty manager at 30 minutes, the other at 45 minutes. The agent alternates between them across runs. What is the failure mode and the smallest first response?",
  ["Context clash: establish precedence or a single source of truth for the escalation rule",
   "Context distraction: compact the conversation history",
   "Context poisoning: delete both procedures from the index",
   "Context confusion: raise top-k so the model sees more candidates"],
  "Two authoritative elements directly disagree, which is a clash. The fix is precedence/one source of truth. Raising top-k adds more conflicting context."),
 ("A2", "1 Foundations",
  "A router must assign each incoming ticket to one of six queues in under 300 ms at high volume. There is no multi-step planning. Which configuration fits?",
  ["Reduced or no extended thinking, short output budget, concise instructions",
   "Extended thinking with a large reasoning budget",
   "Standard reasoning with many long examples of every queue",
   "Split the task across several sub-agents"],
  "Simple, latency-sensitive classification benefits from low token use. Extended thinking and long prompts add cost and context pressure without measured gain."),
 ("A3", "2 Prompt/Genie",
  "A Genie space has correct tables, column descriptions and example SQL, and returns correct numbers for 'trips'. It treats 'peak' as if it were a column name instead of 07:00 to 09:00 and 16:00 to 18:00. What is the smallest effective fix?",
  ["Add a general instruction that defines 'peak'",
   "Add every timetable table to the space",
   "Switch to a larger model",
   "Fine-tune a model on the operator's data"],
  "The data and SQL are right; the business vocabulary is missing. Definitions belong in general instructions. More tables, a bigger model or fine-tuning do not supply a definition."),
 ("A4", "3 Retrieval/Genie",
  "A Victorian user's query returns the NSW variant of a procedure as the top result. The index is fresh and the chunks are well formed. What is the most direct governed fix?",
  ["Push a region metadata filter (the user's region or 'ALL') into the index query",
   "Reduce the chunk size",
   "Add a prompt line asking the model to ignore other regions",
   "Switch the index to continuous sync"],
  "Authority and permission belong in the retrieval query, before the model sees anything. A prompt instruction is not a control, and chunk size or sync mode is unrelated."),
 ("A5", "3 Retrieval/Genie",
  "Amendments to safety procedures must be searchable roughly two minutes after they are saved to the source Delta table. The Delta Sync index is triggered and synced nightly. What change is justified?",
  ["Move to continuous sync, because there is now a real latency requirement",
   "Add a weekly sync",
   "Increase top-k",
   "Recreate the index every night"],
  "Continuous sync is justified only when the latency requirement demands it, and here it does. Rebuilding or syncing less often does not meet a two-minute requirement."),
 ("A6", "3 Retrieval/Genie",
  "Procedures are short, each with a 'Steps' section followed by a 'Conditions' section. Heading-based chunks return the steps without the conditions, and answers omit a safety rule. What is the best change?",
  ["Merge small adjacent sections (or return the parent) so the rule and its conditions stay together",
   "Use smaller chunks so the steps match more precisely",
   "Remove the headings from the documents",
   "Add more overlap to every chunk in the corpus"],
  "The defect is that a rule was separated from its condition. Keep the semantic unit together. Smaller chunks make that worse."),
 ("A7", "4 Memory",
  "An agent must remember a user's preferred answer format across sessions, and must also resume a half-finished investigation after a process restart. Where should each live?",
  ["The preference in a durable keyed store such as Lakebase; the investigation state in durable checkpoint storage",
   "Both in an in-context scratchpad",
   "Both embedded and retrieved by similarity",
   "Both in the conversation history only"],
  "Anything that must survive a session boundary or a restart needs durable, governed storage. A scratchpad or conversation history is lost."),
 ("A8", "4 Memory",
  "A user asks for 'prior incidents similar to intermittent TLS failures after a certificate rotation' and then needs the region and status of each one confirmed. Which approach fits?",
  ["Semantic search to discover candidates, then a structured query to verify region and status",
   "A structured query on the full sentence",
   "Exact string matching on the question text",
   "Load every incident into the context"],
  "Fuzzy 'similar to' is semantic; exact attributes are structured. The hybrid is the common answer."),
 ("A9", "5 Tools/MCP",
  "An agent keeps confusing `get_crew` and `find_crew`, which have almost identical descriptions. What is the first step?",
  ["Clarify or consolidate them, with distinct use and avoid-use conditions",
   "Increase the model temperature",
   "Load both full schemas and rank them after loading",
   "Copy both outputs into long-term memory"],
  "Remove the ambiguity at tool-design time. Ranking after loading pays the token and confusion cost anyway."),
 ("A10", "6 Compaction",
  "After compaction, an agent proposes contacting a vendor that the user explicitly ruled out earlier. What was lost, and what is the fix?",
  ["User constraints and exclusions; retain a deduplicated list of constraints, exclusions and preferences",
   "Raw tool logs; append all tool output to the summary",
   "Chain-of-thought; append the model's reasoning to the summary",
   "Embeddings; rebuild the index"],
  "Constraints are durable task state. Appending raw output or reasoning inflates cost and preserves what should not be kept."),
 ("A11", "7 Multi-agent",
  "Five sub-agents each forecast a product category. After the coordinator updates a key assumption, they keep using the old one. You must not enlarge each sub-agent's context window. Best change?",
  ["Dispatch a bounded handoff packet with a compressed coordinator summary and a freshness marker",
   "Give each sub-agent the full raw coordinator trace",
   "Add more sub-agents",
   "Lower the temperature"],
  "Sub-agents need the updated context, in compact form. The full raw trace blows the window; extra agents or temperature do not carry the update."),
 ("A12", "7 Multi-agent",
  "A task has ten independent document reviews followed by one synthesis. Which design fits?",
  ["Parallel bounded reviewers returning structured results, then source-aware aggregation",
   "One agent reading all documents serially in a single context",
   "Ten agents sharing every raw trace",
   "Ten agents with no output contract"],
  "Independent work parallelises; outputs should be compact and structured so the aggregator is not saturated."),
]

FORM_B = [
 ("B1", "1 Foundations",
  "A long session has accumulated 80 pages of valid but irrelevant logs, and the agent now ignores the user's latest constraint. What is the failure mode and first response?",
  ["Context distraction: scope, clear or compact so the relevant constraint dominates",
   "Context poisoning: remove the logs from the source system",
   "Context clash: choose a winner between the logs",
   "Context confusion: add more tools"],
  "Valid but excessive context is competing for attention. Reduce it; do not 'fix' the source."),
 ("B2", "1 Foundations",
  "State must survive a restart, be auditable, support several concurrent workers and not consume prompt tokens. Where should it live?",
  ["In durable governed storage such as Lakebase or Delta",
   "In the system prompt",
   "In an in-context scratchpad",
   "In the model's weights"],
  "Those requirements describe durable, governed state."),
 ("B3", "2 Prompt/Genie",
  "You have six candidate few-shot examples and a 400-token budget. Which should you include?",
  ["Those that cover an untested tool path, show a required output structure, resolve an ambiguous request, or demonstrate a refusal",
   "The six longest examples",
   "Six near-duplicate examples for consistency",
   "A random sample"],
  "Include examples by marginal contribution. Redundant or low-value examples cost tokens without improving behaviour."),
 ("B4", "3 Retrieval/Genie",
  "An index covers authoritative policy tables and an auto-generated summary table with stale numbers. The agent sometimes cites the stale numbers. What is the first fix?",
  ["Constrain the retrieval space to certified sources with governed views, permissions or tags",
   "Switch to a larger model",
   "Add 'prefer authoritative sources' to the prompt",
   "Increase the chunk size"],
  "Governance defines what can be retrieved. A prompt request is not enforcement, and a bigger model cannot know which table is stale."),
 ("B5", "3 Retrieval/Genie",
  "A nightly pipeline refreshes a Delta table. The triggered Delta Sync index serves yesterday's text. Next-morning freshness is all the business needs. What is the cheapest correct fix?",
  ["Run an index sync as a step after the ingestion pipeline",
   "Drop and recreate the index each night",
   "Switch to continuous sync",
   "Move to a Direct Access index"],
  "Scheduled freshness is satisfied by syncing after ingestion. Rebuilding or continuous sync adds cost without a requirement."),
 ("B6", "4 Memory",
  "A user says 'use a table this time'. Their saved long-term preference is bullet points. Which wins, and why?",
  ["The explicit current instruction, because it is the nearest valid source of intent",
   "The saved preference, because long-term memory is more authoritative",
   "Whichever is longer",
   "A blend of both"],
  "Current explicit intent overrides an older generalised preference."),
 ("B7", "4 Memory",
  "Four MLflow runs report correctness, context recall and faithfulness. The requirement is that no metric falls below 0.85. How should you choose?",
  ["Take runs that meet every threshold, then choose the one with the smallest context or cost",
   "Take the highest mean",
   "Take the run with the single highest metric",
   "Take the run with the smallest variance regardless of level"],
  "Reliability means balanced performance on all required metrics. A mean can hide a failing metric."),
 ("B8", "5 Tools/MCP",
  "An MCP server registers 60 tools and a typical request needs one. Tool-choice accuracy falls as schemas are added. What is the best first change?",
  ["Staged discovery: capability summaries, intent match, then load a single best-fit schema",
   "Move to a larger context window",
   "Add few-shot examples for every tool",
   "Load all schemas and rank them"],
  "Progressive disclosure limits both tokens and ambiguity before selection."),
 ("B9", "5 Tools/MCP",
  "A system prompt carries 4,000 tokens of instructions for a capability used in about 1% of requests. What is the best architecture?",
  ["Package it as an on-demand Agent Skill",
   "Keep it in the always-on prompt",
   "Add more examples to the base prompt",
   "Store it in conversation history"],
  "Rarely used instructions should cost tokens only when relevant."),
 ("B10", "6 Compaction",
  "Which content is safest to clear from context once a summary exists?",
  ["Duplicate verbose tool payloads whose needed facts and provenance ids were already extracted",
   "The user's accepted constraints",
   "Unresolved dependencies",
   "The user's goal"],
  "Remove what is redundant after the needed state is preserved, never the state itself."),
 ("B11", "6 Compaction",
  "You are tuning a compaction prompt. In what order should you optimise?",
  ["Recall first (every task-critical category survives), then precision (remove duplication and verbosity)",
   "Precision first, then recall",
   "Minimise tokens above all",
   "Add the model's chain-of-thought for fidelity"],
  "A summary that drops a critical category cannot be repaired by tightening it. Reasoning traces are not preserved."),
 ("B12", "7 Multi-agent",
  "Agents hand off after every micro-step, each handoff summary loses detail, and coordination dominates cost. What is the diagnosis?",
  ["Boundaries are too fine: merge tightly coupled steps to avoid repeated handoff compression",
   "There are too few agents",
   "The temperature is too high",
   "The index is stale"],
  "Over-fragmentation causes repeated compression and information loss."),
]

COURSE = [
 ("C1", "Course: evaluation",
  "On your test set every answer is correct, but traces show superseded and draft chunks in almost every retrieval. What does this tell you?",
  ["Output-only evaluation is hiding context contamination; add a context-level scorer and a threshold",
   "The system is ready to ship",
   "You need a larger model",
   "Lowering top-k alone is sufficient and needs no measurement"],
  "A correct answer built on contaminated context is luck. Measure the context itself."),
 ("C2", "Course: security",
  "A document marked `current` from an unapproved origin states that a safety rule has been withdrawn. It contains no instructions to the assistant. Which defence stops it?",
  ["A provenance gate that only admits approved origins before the model sees any content",
   "A keyword scanner for phrases such as 'ignore previous instructions'",
   "A system prompt saying evidence is untrusted data",
   "Setting temperature to zero"],
  "There is no instruction to detect and the claim looks authoritative. Only controlling which sources may enter context stops a poisoned fact."),
]

def _shuffle_all(form_id, items, salt):
    rnd = random.Random(f"ce-quiz-{form_id}-{salt}")
    orders = []
    for _ in items:
        o = list(range(4)); rnd.shuffle(o); orders.append(o)
    return orders

def _balanced_orders(form_id, items):
    """Find a shuffle where each answer letter is used a balanced number of times (no guessable skew)."""
    n = len(items)
    lo, hi = (n // 4) - 1, (n + 3) // 4 + 1
    for salt in range(10000):
        orders = _shuffle_all(form_id, items, salt)
        counts = [sum(1 for o in orders if o.index(0) == k) for k in range(4)]
        if n < 8 or (min(counts) >= lo and max(counts) <= hi):
            return orders
    return _shuffle_all(form_id, items, 0)

def render(form_id, title, items, with_key):
    orders = _balanced_orders(form_id, items)
    out = [f"# {title}", "", "Choose the single best answer unless told otherwise. Scenario-style: pick the smallest governed fix for the stated requirement.", ""]
    key = []
    letters = "ABCD"
    for (qid, dom, stem, opts, why), order in zip(items, orders):
        correct = letters[order.index(0)]
        out += [f"**{qid}.** _{dom}_  {stem}", ""] + [f"- {letters[i]}. {opts[o]}" for i, o in enumerate(order)] + [""]
        key.append((qid, dom, correct, why))
    return "\n".join(out), key

here = pathlib.Path(__file__).parent
a_txt, a_key = render("A", "Context Engineering: Form A (pre-course, 12 questions)", FORM_A, True)
b_txt, b_key = render("B", "Context Engineering: Form B (post-course, 12 questions)", FORM_B, True)
c_txt, c_key = render("C", "Course-specific questions (bonus, not in the exam blueprint)", COURSE, True)
(here / "quiz_form_A_pre.md").write_text(a_txt + "\n")
(here / "quiz_form_B_post.md").write_text(b_txt + "\n")
(here / "quiz_course_specific.md").write_text(c_txt + "\n")
key_md = ["# Answer key and rationale (FACILITATOR ONLY)", "", "Forms A and B are parallel: same domain mix, different scenarios, so a pre/post gain is not just memory of the questions.", ""]
for name, k in (("Form A", a_key), ("Form B", b_key), ("Course-specific", c_key)):
    key_md += [f"## {name}", "", "| Q | Domain | Key | Why |", "|---|---|---|---|"] + [f"| {q} | {d} | **{c}** | {w} |" for q, d, c, w in k] + [""]
(here / "answer_key.md").write_text("\n".join(key_md))
from collections import Counter
print("Form A keys:", Counter(c for _, _, c, _ in a_key), "| Form B keys:", Counter(c for _, _, c, _ in b_key))
print("written:", [p.name for p in sorted(here.glob("*.md"))])
