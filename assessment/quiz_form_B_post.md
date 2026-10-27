# Context Engineering: Form B (post-course, 12 questions)

Choose the single best answer unless told otherwise. Scenario-style: pick the smallest governed fix for the stated requirement.

**B1.** _1 Foundations_  A long session has accumulated 80 pages of valid but irrelevant logs, and the agent now ignores the user's latest constraint. What is the failure mode and first response?

- A. Context distraction: scope, clear or compact so the relevant constraint dominates
- B. Context poisoning: remove the logs from the source system
- C. Context confusion: add more tools
- D. Context clash: choose a winner between the logs

**B2.** _1 Foundations_  State must survive a restart, be auditable, support several concurrent workers and not consume prompt tokens. Where should it live?

- A. In durable governed storage such as Lakebase or Delta
- B. In an in-context scratchpad
- C. In the model's weights
- D. In the system prompt

**B3.** _2 Prompt/Genie_  You have six candidate few-shot examples and a 400-token budget. Which should you include?

- A. Six near-duplicate examples for consistency
- B. The six longest examples
- C. Those that cover an untested tool path, show a required output structure, resolve an ambiguous request, or demonstrate a refusal
- D. A random sample

**B4.** _3 Retrieval/Genie_  An index covers authoritative policy tables and an auto-generated summary table with stale numbers. The agent sometimes cites the stale numbers. What is the first fix?

- A. Switch to a larger model
- B. Add 'prefer authoritative sources' to the prompt
- C. Increase the chunk size
- D. Constrain the retrieval space to certified sources with governed views, permissions or tags

**B5.** _3 Retrieval/Genie_  A nightly pipeline refreshes a Delta table. The triggered Delta Sync index serves yesterday's text. Next-morning freshness is all the business needs. What is the cheapest correct fix?

- A. Switch to continuous sync
- B. Run an index sync as a step after the ingestion pipeline
- C. Drop and recreate the index each night
- D. Move to a Direct Access index

**B6.** _4 Memory_  A user says 'use a table this time'. Their saved long-term preference is bullet points. Which wins, and why?

- A. The saved preference, because long-term memory is more authoritative
- B. Whichever is longer
- C. The explicit current instruction, because it is the nearest valid source of intent
- D. A blend of both

**B7.** _4 Memory_  Four MLflow runs report correctness, context recall and faithfulness. The requirement is that no metric falls below 0.85. How should you choose?

- A. Take runs that meet every threshold, then choose the one with the smallest context or cost
- B. Take the run with the single highest metric
- C. Take the run with the smallest variance regardless of level
- D. Take the highest mean

**B8.** _5 Tools/MCP_  An MCP server registers 60 tools and a typical request needs one. Tool-choice accuracy falls as schemas are added. What is the best first change?

- A. Add few-shot examples for every tool
- B. Load all schemas and rank them
- C. Move to a larger context window
- D. Staged discovery: capability summaries, intent match, then load a single best-fit schema

**B9.** _5 Tools/MCP_  A system prompt carries 4,000 tokens of instructions for a capability used in about 1% of requests. What is the best architecture?

- A. Add more examples to the base prompt
- B. Store it in conversation history
- C. Keep it in the always-on prompt
- D. Package it as an on-demand Agent Skill

**B10.** _6 Compaction_  Which content is safest to clear from context once a summary exists?

- A. Duplicate verbose tool payloads whose needed facts and provenance ids were already extracted
- B. Unresolved dependencies
- C. The user's accepted constraints
- D. The user's goal

**B11.** _6 Compaction_  You are tuning a compaction prompt. In what order should you optimise?

- A. Precision first, then recall
- B. Recall first (every task-critical category survives), then precision (remove duplication and verbosity)
- C. Minimise tokens above all
- D. Add the model's chain-of-thought for fidelity

**B12.** _7 Multi-agent_  Agents hand off after every micro-step, each handoff summary loses detail, and coordination dominates cost. What is the diagnosis?

- A. The index is stale
- B. The temperature is too high
- C. There are too few agents
- D. Boundaries are too fine: merge tightly coupled steps to avoid repeated handoff compression

