# Answer key and rationale (FACILITATOR ONLY)

Forms A and B are parallel: same domain mix, different scenarios, so a pre/post gain is not just memory of the questions.

## Form A

| Q | Domain | Key | Why |
|---|---|---|---|
| A1 | 1 Foundations | **C** | Two authoritative elements directly disagree, which is a clash. The fix is precedence/one source of truth. Raising top-k adds more conflicting context. |
| A2 | 1 Foundations | **C** | Simple, latency-sensitive classification benefits from low token use. Extended thinking and long prompts add cost and context pressure without measured gain. |
| A3 | 2 Prompt/Genie | **A** | The data and SQL are right; the business vocabulary is missing. Definitions belong in general instructions. More tables, a bigger model or fine-tuning do not supply a definition. |
| A4 | 3 Retrieval/Genie | **C** | Authority and permission belong in the retrieval query, before the model sees anything. A prompt instruction is not a control, and chunk size or sync mode is unrelated. |
| A5 | 3 Retrieval/Genie | **B** | Continuous sync is justified only when the latency requirement demands it, and here it does. Rebuilding or syncing less often does not meet a two-minute requirement. |
| A6 | 3 Retrieval/Genie | **D** | The defect is that a rule was separated from its condition. Keep the semantic unit together. Smaller chunks make that worse. |
| A7 | 4 Memory | **A** | Anything that must survive a session boundary or a restart needs durable, governed storage. A scratchpad or conversation history is lost. |
| A8 | 4 Memory | **D** | Fuzzy 'similar to' is semantic; exact attributes are structured. The hybrid is the common answer. |
| A9 | 5 Tools/MCP | **B** | Remove the ambiguity at tool-design time. Ranking after loading pays the token and confusion cost anyway. |
| A10 | 6 Compaction | **C** | Constraints are durable task state. Appending raw output or reasoning inflates cost and preserves what should not be kept. |
| A11 | 7 Multi-agent | **B** | Sub-agents need the updated context, in compact form. The full raw trace blows the window; extra agents or temperature do not carry the update. |
| A12 | 7 Multi-agent | **A** | Independent work parallelises; outputs should be compact and structured so the aggregator is not saturated. |

## Form B

| Q | Domain | Key | Why |
|---|---|---|---|
| B1 | 1 Foundations | **A** | Valid but excessive context is competing for attention. Reduce it; do not 'fix' the source. |
| B2 | 1 Foundations | **A** | Those requirements describe durable, governed state. |
| B3 | 2 Prompt/Genie | **C** | Include examples by marginal contribution. Redundant or low-value examples cost tokens without improving behaviour. |
| B4 | 3 Retrieval/Genie | **D** | Governance defines what can be retrieved. A prompt request is not enforcement, and a bigger model cannot know which table is stale. |
| B5 | 3 Retrieval/Genie | **B** | Scheduled freshness is satisfied by syncing after ingestion. Rebuilding or continuous sync adds cost without a requirement. |
| B6 | 4 Memory | **C** | Current explicit intent overrides an older generalised preference. |
| B7 | 4 Memory | **A** | Reliability means balanced performance on all required metrics. A mean can hide a failing metric. |
| B8 | 5 Tools/MCP | **D** | Progressive disclosure limits both tokens and ambiguity before selection. |
| B9 | 5 Tools/MCP | **D** | Rarely used instructions should cost tokens only when relevant. |
| B10 | 6 Compaction | **A** | Remove what is redundant after the needed state is preserved, never the state itself. |
| B11 | 6 Compaction | **B** | A summary that drops a critical category cannot be repaired by tightening it. Reasoning traces are not preserved. |
| B12 | 7 Multi-agent | **D** | Over-fragmentation causes repeated compression and information loss. |

## Course-specific

| Q | Domain | Key | Why |
|---|---|---|---|
| C1 | Course: evaluation | **D** | A correct answer built on contaminated context is luck. Measure the context itself. |
| C2 | Course: security | **A** | There is no instruction to detect and the claim looks authoritative. Only controlling which sources may enter context stops a poisoned fact. |
