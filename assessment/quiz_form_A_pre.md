# Context Engineering: Form A (pre-course, 12 questions)

Choose the single best answer unless told otherwise. Scenario-style: pick the smallest governed fix for the stated requirement.

**A1.** _1 Foundations_  A control-room agent retrieves two procedures for the same task. Both are marked current and approved: one says escalate to the duty manager at 30 minutes, the other at 45 minutes. The agent alternates between them across runs. What is the failure mode and the smallest first response?

- A. Context confusion: raise top-k so the model sees more candidates
- B. Context poisoning: delete both procedures from the index
- C. Context clash: establish precedence or a single source of truth for the escalation rule
- D. Context distraction: compact the conversation history

**A2.** _1 Foundations_  A router must assign each incoming ticket to one of six queues in under 300 ms at high volume. There is no multi-step planning. Which configuration fits?

- A. Extended thinking with a large reasoning budget
- B. Split the task across several sub-agents
- C. Reduced or no extended thinking, short output budget, concise instructions
- D. Standard reasoning with many long examples of every queue

**A3.** _2 Prompt/Genie_  A Genie space has correct tables, column descriptions and example SQL, and returns correct numbers for 'trips'. It treats 'peak' as if it were a column name instead of 07:00 to 09:00 and 16:00 to 18:00. What is the smallest effective fix?

- A. Add a general instruction that defines 'peak'
- B. Switch to a larger model
- C. Add every timetable table to the space
- D. Fine-tune a model on the operator's data

**A4.** _3 Retrieval/Genie_  A Victorian user's query returns the NSW variant of a procedure as the top result. The index is fresh and the chunks are well formed. What is the most direct governed fix?

- A. Switch the index to continuous sync
- B. Reduce the chunk size
- C. Push a region metadata filter (the user's region or 'ALL') into the index query
- D. Add a prompt line asking the model to ignore other regions

**A5.** _3 Retrieval/Genie_  Amendments to safety procedures must be searchable roughly two minutes after they are saved to the source Delta table. The Delta Sync index is triggered and synced nightly. What change is justified?

- A. Add a weekly sync
- B. Move to continuous sync, because there is now a real latency requirement
- C. Recreate the index every night
- D. Increase top-k

**A6.** _3 Retrieval/Genie_  Procedures are short, each with a 'Steps' section followed by a 'Conditions' section. Heading-based chunks return the steps without the conditions, and answers omit a safety rule. What is the best change?

- A. Add more overlap to every chunk in the corpus
- B. Use smaller chunks so the steps match more precisely
- C. Remove the headings from the documents
- D. Merge small adjacent sections (or return the parent) so the rule and its conditions stay together

**A7.** _4 Memory_  An agent must remember a user's preferred answer format across sessions, and must also resume a half-finished investigation after a process restart. Where should each live?

- A. The preference in a durable keyed store such as Lakebase; the investigation state in durable checkpoint storage
- B. Both in an in-context scratchpad
- C. Both in the conversation history only
- D. Both embedded and retrieved by similarity

**A8.** _4 Memory_  A user asks for 'prior incidents similar to intermittent TLS failures after a certificate rotation' and then needs the region and status of each one confirmed. Which approach fits?

- A. A structured query on the full sentence
- B. Load every incident into the context
- C. Exact string matching on the question text
- D. Semantic search to discover candidates, then a structured query to verify region and status

**A9.** _5 Tools/MCP_  An agent keeps confusing `get_crew` and `find_crew`, which have almost identical descriptions. What is the first step?

- A. Load both full schemas and rank them after loading
- B. Clarify or consolidate them, with distinct use and avoid-use conditions
- C. Increase the model temperature
- D. Copy both outputs into long-term memory

**A10.** _6 Compaction_  After compaction, an agent proposes contacting a vendor that the user explicitly ruled out earlier. What was lost, and what is the fix?

- A. Raw tool logs; append all tool output to the summary
- B. Embeddings; rebuild the index
- C. User constraints and exclusions; retain a deduplicated list of constraints, exclusions and preferences
- D. Chain-of-thought; append the model's reasoning to the summary

**A11.** _7 Multi-agent_  Five sub-agents each forecast a product category. After the coordinator updates a key assumption, they keep using the old one. You must not enlarge each sub-agent's context window. Best change?

- A. Lower the temperature
- B. Dispatch a bounded handoff packet with a compressed coordinator summary and a freshness marker
- C. Add more sub-agents
- D. Give each sub-agent the full raw coordinator trace

**A12.** _7 Multi-agent_  A task has ten independent document reviews followed by one synthesis. Which design fits?

- A. Parallel bounded reviewers returning structured results, then source-aware aggregation
- B. One agent reading all documents serially in a single context
- C. Ten agents with no output contract
- D. Ten agents sharing every raw trace

