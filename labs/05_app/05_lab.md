# Lab 5 · A governed, App-backed agent experience

**Time:** 50 min core · **Maps to exam:** Domain 1 (product selection), Domain 3 (constraining the retrieval space), Domain 4 (memory source), Domain 5 (tool/approval design)
**Code:** `app/ce-gridworks-assistant/` (AppKit: Node/React). **Tiers:** *Core* = Parts 1 to 4 on the facilitator's deployed app. *Skip-ahead* = read Part 5 only. *Stretch* = Part 6, change the code.

> Illustrative. The AI Search plugin is **beta** (`@databricks/appkit/beta`) and AppKit APIs change between minor releases. Check `npx @databricks/appkit docs` for the version you scaffold.
> This lab teaches the *same context-engineering patterns* as Labs 3 to 6 in TypeScript. It does not reuse the Python/LangGraph code.

## The point of this lab
Context engineering does not stop at the notebook. The **product surface** decides what intent is captured, whose identity runs the query, what the user can inspect, and which side effects need a human. Every decision below is a context decision.

## Part 1 · Read the identity banner (5 min)
Open the app. The header shows who you are and **"Runs as: app service principal"**.
1. Whose permissions does the retrieval use: yours or the app's? Why does that matter if two users in different regions use the same app?
2. Find the three tables the KPI panel reads. Open `databricks.yml` and list the app's `uc_securable` resources. Which tables are **absent**, and what happens if someone adds `raw_inspection_export` to the SQL?
3. (Discuss) When would you switch a surface to on-behalf-of-user? What would you lose (shared caching, simplicity)?

## Part 2 · Governed vs ungoverned context (15 min)
Ask: *"What must happen when isolating a critical 33kV feeder?"* with region **VIC**.
1. Run it with **Governed context ON**. Open **How this context was built**. Record: filter, chunks, characters, what governance removed.
2. Turn governance **OFF** and ask again. Record the same fields. Which chunks reached the model that should not have?
3. Did the *answer* change much? If not, why is it still a problem? (Hint: Lab 6, `authority_safe`.)
4. Ask *"What is the earth resistance limit?"* in both modes. What is the only document that mentions it, and what is its status?
5. Switch region to **NSW** and repeat Question 1. What differs, and which document supplied it?

**Expected:** governed context is smaller and contains only current, region-permitted chunks; ungoverned context lets a superseded and a wrong-region procedure reach the model.

## Part 3 · Memory with the right lifetime (10 min)
1. In **Your memory**, save *numbered steps*. Reload the page: it persists (Lakebase, exact key lookup).
2. Ask a question with **Format for this session** left on the default. Check the "Format … from" line.
3. Set the session format to *short paragraph* and ask again. Which source won, and why is that the right precedence?
4. Why is the preference an **enumerated** choice rather than free text? What attack does that prevent?

## Part 4 · The approval gate (10 min)
1. Click **Request reinspection** on a feeder. Click it again. How many requests exist? Which database feature guarantees that?
2. **Approve** it. Try to approve it again (use the browser network tab or ask the facilitator to). What happens, and why does the server, not the button, enforce this?
3. The demo lets you approve your own request. Write one sentence on how you would enforce separation of duties.

## Part 5 · Design review (10 min, pairs)
One person is the **context engineer**, the other is the **risk reviewer**. Fill in the table for this app:

| Context element | Source | Authority | Lifetime | Where it lives |
|---|---|---|---|---|
| Procedures / standards | ? | ? | ? | ? |
| KPIs | ? | ? | ? | ? |
| Response-format preference | ? | ? | ? | ? |
| Approval decision | ? | ? | ? | ? |
| Chat answers and what they were built from | ? | ? | ? | ? |

Then answer: *which single change would most reduce the risk of a wrong answer being acted on?*

## Part 6 · Stretch (code)
Pick one, make the change in `server/`, redeploy to **your own** app name, and prove it with a request:
- Add an `INSUFFICIENT EVIDENCE` rule for empty governed retrieval (compare with config D in Lab 6; what does it cost?).
- Add a `region` to the stored preference and use it as the default filter.
- Record each turn's retrieved ids as an MLflow trace instead of only a Lakebase row.

## Checks (facilitator-run)
- [ ] Governed answer never lists a `superseded`, `draft` or wrong-region source
- [ ] Ungoverned mode lists at least one contaminated source for the isolation question
- [ ] Saved preference survives a reload; session choice overrides it
- [ ] Two clicks create one pending request; a second decision returns 409
- [ ] A free-text preference value is rejected (400)

## Debrief
- **Exam link (Domain 3):** *design a governance strategy that constrains the agent's retrieval space to authoritative sources before deployment*. The filter lives in the **index query**, not in the prompt.
- **Exam link (Domain 4):** use the nearest valid memory source. Current explicit intent beats an older preference.
- **Partner takeaway:** what the user can *see* (sources, filters, identity) is part of the product's trustworthiness, and it is also what makes evaluation and incident review possible.
