"""Genie test harness shared by Lab 2 (notebook) and local runs.

`api(method, path, body=None) -> dict` is injected so the same code runs in a notebook
(WorkspaceClient.api_client.do) and from a terminal (databricks CLI). Illustrative: Genie API
paths and response fields can change; verify against the current Genie API docs.
"""
from __future__ import annotations
import json, time

CAT, SH = "gsethi", "ce_shared"
T = f"{CAT}.{SH}"

# (question, expected scalar, tolerance). Expected values are computed from the generated data.
TEST_SET = [
    ("How many priority two outages did Victoria have in September 2026?", 22, 0),
    ("What was the SAIDI for unplanned outages?", 86.143, 0.5),
    ("How many critical feeders are in poor health?", 4, 0),
    ("As of 27 October 2026, how many assets are overdue for inspection?", 240, 0),
    ("How many HV switching crews are available on 28 October 2026?", 7, 0),
    ("How many open P1 work orders are there?", 74, 0),
]

TABLES = sorted([f"{T}.gold_asset_health", f"{T}.gold_outage_events", f"{T}.gold_work_orders",
                 f"{T}.gold_crews", f"{T}.gold_crew_availability"])


def _id(n: int) -> str:
    return f"{n:032x}"


def space_json(*, instructions: list[str] | None = None, example_sqls: list[tuple[str, str]] | None = None,
               filters: list[dict] | None = None, measures: list[dict] | None = None,
               sample_questions: list[str] | None = None) -> str:
    """Build the serialized Genie space. Each Genie control is a separate argument on purpose."""
    n = iter(range(1, 1000))
    ser: dict = {"version": 2, "data_sources": {"tables": [{"identifier": t} for t in TABLES]}}
    if sample_questions:
        ser["config"] = {"sample_questions": [{"id": _id(next(n)), "question": [q]} for q in sample_questions]}
    ins: dict = {}
    if instructions:
        ins["text_instructions"] = [{"id": _id(next(n)), "content": instructions}]
    if example_sqls:
        ins["example_question_sqls"] = [{"id": _id(next(n)), "question": [q], "sql": [s]} for q, s in example_sqls]
    snippets: dict = {}
    if filters:
        snippets["filters"] = [{"id": _id(next(n)), "sql": [f["sql"]], "display_name": f["name"],
                                "synonyms": f.get("synonyms", [])} for f in filters]
    if measures:
        snippets["measures"] = [{"id": _id(next(n)), "sql": [m["sql"]], "display_name": m["name"],
                                 "alias": m["alias"]} for m in measures]
    if snippets:
        ins["sql_snippets"] = snippets
    if ins:
        ser["instructions"] = ins
    return json.dumps(ser)


def create_space(api, title: str, warehouse_id: str, parent_path: str, serialized: str) -> str:
    r = api("POST", "/api/2.0/genie/spaces", {"title": title, "description": "Context Engineering lab (fictional data)",
                                              "warehouse_id": warehouse_id, "parent_path": parent_path,
                                              "serialized_space": serialized})
    return r["space_id"]


def update_space(api, space_id: str, serialized: str) -> None:
    api("PATCH", f"/api/2.0/genie/spaces/{space_id}", {"serialized_space": serialized})


def ask(api, space_id: str, question: str, timeout_s: int = 150) -> dict:
    r = api("POST", f"/api/2.0/genie/spaces/{space_id}/start-conversation", {"content": question})
    cid, mid = r["conversation_id"], r["message_id"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        m = api("GET", f"/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}")
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    out = {"status": m.get("status"), "sql": None, "value": None, "text": None}
    for a in m.get("attachments", []):
        if "query" in a and out["sql"] is None:
            out["sql"] = a["query"].get("query")
            res = api("GET", f"/api/2.0/genie/spaces/{space_id}/conversations/{cid}/messages/{mid}"
                             f"/attachments/{a['attachment_id']}/query-result")
            rows = res.get("statement_response", {}).get("result", {}).get("data_array") or []
            if rows and rows[0]:
                try:
                    out["value"] = float(rows[0][0])
                except (TypeError, ValueError):
                    out["value"] = rows[0][0]
        if "text" in a:
            out["text"] = a["text"].get("content")
    return out


def run_suite(api, space_id: str, test_set=TEST_SET, verbose: bool = True) -> dict:
    results = []
    for q, expected, tol in test_set:
        try:
            got = ask(api, space_id, q)
        except Exception as e:  # keep the suite running
            got = {"status": "ERROR", "value": None, "sql": None, "text": str(e)[:120]}
        ok = isinstance(got["value"], float) and abs(got["value"] - expected) <= tol
        results.append({"question": q, "expected": expected, "got": got["value"], "pass": ok, "sql": got["sql"]})
        if verbose:
            print(("PASS " if ok else "FAIL ") + f"{q[:70]:70s} expected={expected} got={got['value']}")
    passed = sum(r["pass"] for r in results)
    print(f"\n{passed}/{len(results)} correct")
    return {"passed": passed, "total": len(results), "results": results}
