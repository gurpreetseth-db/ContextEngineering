# Session decks (HTML)

Three self-contained HTML decks, Databricks-branded, for the ANZ partner enablement. Open in any browser; no build tools needed to *present*.

| File | Slides | Session |
|---|---:|---|
| `session1_foundations_governance_genie.html` | 15 | Foundations, governance, Genie (Labs 1 and 2) |
| `session2_retrieval_memory_tools.html` | 18 | Retrieval, memory, tools, compaction (Labs 3 and 4, injection demo) |
| `session3_multiagent_runtime_apps_eval.html` | 15 | Multi-agent, gateway, app, evaluation (Labs 5 and 6, capstone) |

## Presenting
- **Arrow keys / Space** advance, **Home / End** jump, click the dots on the right, or swipe.
- Press **N** to show or hide **speaker notes** for the current slide. Notes carry the facilitator talk track, exam notes, and traps from `facilitator-guide/facilitator_guide.md`.
- Fonts load from Google Fonts and fall back to system fonts offline.
- To save a PDF, use the skill's exporter (`export-pdf.js`, Puppeteer) or the browser's Print.

## Editing
Slide text lives in `_build/deck_1.py`, `deck_2.py`, `deck_3.py`. Rebuild with:
```bash
python3 slides/_build/build.py
```
`_build/lib.py` holds the page template and slide-type helpers; `brand.css` is extracted from the Databricks brand system; `a11y.css` raises small red text to WCAG AA.

## Quality checks run on every slide
At 1920x1080 and 1366x768: no content overflow, no horizontal overflow, no JavaScript errors, and every piece of text at WCAG AA contrast (4.5:1 small, 3:1 large) against its real rendered background. All three decks pass. Data slides were also reviewed by eye.

## Known limits
- Densest slides carry up to ~74 words (the 9-row stack reference table and the promise slide); most are 45 to 65. The skill's limit for card slides is 60.
- Every number on a slide is a measured result recorded in `docs/00_fact_sheet.md` (one model, small samples; the injection demo says so on the slide). Refresh them if you re-run the labs on a different model.
- Genie Ontology is labelled as a preview capability; gateway features are marked "verify GA or preview per feature". Re-check both before each cohort.
- Not tested on a projector or in presenter-display mode; try a dry run on the venue's screen.
