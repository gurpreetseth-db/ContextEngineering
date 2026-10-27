# Course-specific questions (bonus, not in the exam blueprint)

Choose the single best answer unless told otherwise. Scenario-style: pick the smallest governed fix for the stated requirement.

**C1.** _Course: evaluation_  On your test set every answer is correct, but traces show superseded and draft chunks in almost every retrieval. What does this tell you?

- A. You need a larger model
- B. Lowering top-k alone is sufficient and needs no measurement
- C. The system is ready to ship
- D. Output-only evaluation is hiding context contamination; add a context-level scorer and a threshold

**C2.** _Course: security_  A document marked `current` from an unapproved origin states that a safety rule has been withdrawn. It contains no instructions to the assistant. Which defence stops it?

- A. A provenance gate that only admits approved origins before the model sees any content
- B. A system prompt saying evidence is untrusted data
- C. A keyword scanner for phrases such as 'ignore previous instructions'
- D. Setting temperature to zero

