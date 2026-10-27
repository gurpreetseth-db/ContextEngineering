"""ANZ GridWorks synthetic data generator (stdlib only, deterministic).

Produces the tables and documents behind every lab. The data is deliberately messy:
raw / derived / draft / certified assets coexist so Lab 1 has something to curate, and the
document corpus contains superseded and regional variants so Lab 3 has something to filter.

Everything here is fictional. No real customer, employee or network data is used.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta

SEED = 20261027
REGIONS = {"VIC": "Victoria", "NSW": "New South Wales", "QLD": "Queensland", "SA": "South Australia"}
ASSET_CLASSES = ["33kV_feeder", "11kV_feeder", "zone_substation", "distribution_transformer", "pole_top_switch"]
CAUSES = ["vegetation", "equipment_failure", "weather", "third_party_damage", "planned_work", "unknown"]
TODAY = date(2026, 10, 27)


def _rng() -> random.Random:
    return random.Random(SEED)


def _ts(rng: random.Random, start: date, days: int) -> datetime:
    return datetime.combine(start, datetime.min.time()) + timedelta(
        days=rng.randrange(days), minutes=rng.randrange(24 * 60)
    )


def build_assets(rng: random.Random, n: int = 400) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        region = rng.choices(list(REGIONS), weights=[4, 4, 3, 2])[0]
        cls = rng.choices(ASSET_CLASSES, weights=[2, 4, 1, 6, 4])[0]
        last_insp = TODAY - timedelta(days=rng.randrange(20, 900))
        score = max(5, min(100, int(rng.gauss(72, 18))))
        rows.append({
            "asset_id": f"A-{i:04d}",
            "asset_class": cls,
            "region_code": region,
            "is_critical_feeder": cls in ("33kV_feeder", "11kV_feeder") and rng.random() < 0.35,
            "health_score": score,
            "health_band": "poor" if score < 50 else "fair" if score < 75 else "good",
            "last_inspection_date": last_insp,
            "next_inspection_due_date": last_insp + timedelta(days=365 if score >= 50 else 180),
            "is_current": True,
        })
    return rows


def build_outages(rng: random.Random, assets: list[dict], n: int = 3000) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        a = rng.choice(assets)
        start = _ts(rng, date(2025, 11, 1), 360)
        planned = rng.random() < 0.3
        dur = max(5, int(rng.lognormvariate(4.2, 0.9)))
        cust = int(rng.lognormvariate(5.5, 1.0))
        rows.append({
            "outage_id": f"OUT-{i:06d}",
            "asset_id": a["asset_id"],
            "region_code": a["region_code"],
            "event_start_ts": start,
            "event_end_ts": start + timedelta(minutes=dur),
            "is_planned": planned,
            "priority_code": rng.choices(["P1", "P2", "P3"], weights=[1, 3, 6])[0],
            "cause": "planned_work" if planned else rng.choice([c for c in CAUSES if c != "planned_work"]),
            "customers_interrupted": cust,
        })
    return rows


def build_work_orders(rng: random.Random, assets: list[dict], n: int = 1500) -> list[dict]:
    statuses = ["open", "in_progress", "complete", "cancelled"]
    rows = []
    for i in range(1, n + 1):
        a = rng.choice(assets)
        created = _ts(rng, date(2026, 1, 1), 300)
        rows.append({
            "work_order_id": 1000 + i,
            "asset_id": a["asset_id"],
            "region_code": a["region_code"],
            "status": rng.choices(statuses, weights=[3, 2, 5, 1])[0],
            "priority_code": rng.choices(["P1", "P2", "P3"], weights=[1, 3, 6])[0],
            "work_type": rng.choice(["inspection", "repair", "vegetation_clearing", "replacement"]),
            "created_ts": created,
            "amount_aud": round(rng.lognormvariate(8.2, 0.9), 2),
        })
    return rows


def build_crews(rng: random.Random, n: int = 40) -> tuple[list[dict], list[dict]]:
    crews, avail = [], []
    for i in range(1, n + 1):
        region = rng.choice(list(REGIONS))
        crews.append({"crew_id": f"C-{i:03d}", "region_code": region,
                      "skill": rng.choice(["HV_switching", "line_work", "vegetation", "substation"])})
        for d in range(14):
            avail.append({"crew_id": f"C-{i:03d}", "work_date": TODAY + timedelta(days=d),
                          "available": rng.random() < 0.7})
    return crews, avail


# ---------------------------------------------------------------- deliberately messy variants
def messy_raw_outages(rng: random.Random, certified: list[dict]) -> list[dict]:
    """Raw ingest: inconsistent region spellings, duplicate rows, free-text priority."""
    spell = {"VIC": ["VIC", "Vic", "victoria"], "NSW": ["NSW", "nsw", "New South Wales"],
             "QLD": ["QLD", "qld"], "SA": ["SA", "S.A."]}
    pri = {"P1": ["P1", "priority one", "1"], "P2": ["P2", "priority two", "2"], "P3": ["P3", "priority three", "3"]}
    out = []
    for r in certified:
        row = dict(r)
        row["region_code"] = rng.choice(spell[r["region_code"]])
        row["priority_code"] = rng.choice(pri[r["priority_code"]])
        row["ingest_ts"] = r["event_start_ts"] + timedelta(hours=rng.randrange(1, 48))
        out.append(row)
        if rng.random() < 0.04:  # duplicates
            out.append(dict(row))
    return out


def derived_rollup(outages: list[dict]) -> list[dict]:
    """A stale derived rollup built with a WRONG SAIDI formula (ignores customer weighting)."""
    by: dict[tuple, list] = {}
    for o in outages:
        by.setdefault((o["region_code"], o["event_start_ts"].strftime("%Y-%m")), []).append(o)
    rows = []
    for (region, month), v in sorted(by.items()):
        mins = [(o["event_end_ts"] - o["event_start_ts"]).total_seconds() / 60 for o in v]
        rows.append({"region_code": region, "month": month, "events": len(v),
                     "saidi_minutes": round(sum(mins) / len(mins), 2),  # wrong on purpose
                     "built_on": date(2026, 3, 1)})
    return rows


def draft_summary(outages: list[dict]) -> list[dict]:
    """WIP table: half-finished, one region only."""
    return [{"region_code": "VIC", "p2_events": sum(1 for o in outages
            if o["region_code"] == "VIC" and o["priority_code"] == "P2"), "status": "DRAFT - do not use"}]


def raw_inspection_export(rng: random.Random, assets: list[dict]) -> list[dict]:
    """Contains technician PII - the reason a curated view must exist."""
    first = ["Alex", "Sam", "Jordan", "Priya", "Wei", "Mia", "Noah", "Aroha"]
    last = ["Nguyen", "Smith", "Patel", "Brown", "Singh", "Wilson", "Taylor", "Kaur"]
    rows = []
    for a in assets:
        name = f"{rng.choice(first)} {rng.choice(last)}"
        rows.append({**a, "technician_name": name,
                     "technician_mobile": f"04{rng.randrange(10**8):08d}",
                     "customer_contact_email": f"customer{rng.randrange(10**5)}@example.com"})
    return rows


# ---------------------------------------------------------------- document corpus
_DOCS = [
    ("PRC-LOTO-001", "Lockout/Tagout for 33kV feeders", "VIC", "current", date(2026, 6, 1),
     "# Lockout/Tagout — 33kV feeders (Victoria)\n\n## Scope\nApplies to all 33kV feeder isolations in Victoria.\n\n## Steps\n1. Obtain a switching sheet from the control room.\n2. Open the feeder breaker and verify open with a calibrated detector.\n3. Apply personal lock and tag at the isolation point.\n4. Test dead and apply earths on both sides.\n\n## Conditions\nA second competent person must witness steps 2 to 4 when the feeder is classed as a critical feeder."),
    ("PRC-LOTO-001-OLD", "Lockout/Tagout for 33kV feeders", "VIC", "superseded", date(2023, 2, 1),
     "# Lockout/Tagout — 33kV feeders (Victoria) [SUPERSEDED]\n\n1. Open the feeder breaker.\n2. Apply lock and tag.\n3. Apply earths.\n\nNote: witness requirement not yet introduced."),
    ("PRC-LOTO-002", "Lockout/Tagout for 33kV feeders", "NSW", "current", date(2026, 4, 15),
     "# Lockout/Tagout — 33kV feeders (New South Wales)\n\n## Steps\n1. Obtain a switching instruction via the NSW network operations centre.\n2. Open, verify open, lock and tag.\n3. Test dead and earth.\n\n## Conditions\nWitness required for all 33kV isolations, not only critical feeders."),
    ("PRC-VEG-010", "Vegetation clearance distances", "ALL", "current", date(2026, 1, 20),
     "# Vegetation clearance distances\n\n## Minimum clearances\n- 11kV: 1.5 m in standard areas, 2.0 m in bushfire-prone areas.\n- 33kV: 2.5 m in standard areas, 3.0 m in bushfire-prone areas.\n\n## Planned outages\nVegetation work requiring de-energisation is a planned outage and must be notified 4 business days ahead."),
    ("PRC-XFMR-020", "Distribution transformer inspection", "ALL", "current", date(2025, 11, 3),
     "# Distribution transformer inspection\n\nInspect oil level, bushings, earthing and corrosion. Assets scoring below 50 are in the poor health band and must be reinspected within 180 days; all others within 365 days. Record the inspection date as last inspection."),
    ("PRC-SAFE-030", "Priority classification of outages", "ALL", "current", date(2026, 2, 10),
     "# Priority classification\n\n- P1 (priority one): public safety risk or loss of supply to critical infrastructure.\n- P2 (priority two): loss of supply to more than 500 customers or a critical feeder out of service.\n- P3 (priority three): all other events.\n\nPriority two is also written P2."),
    ("PRC-SAIDI-040", "Reliability metric definitions", "ALL", "current", date(2026, 3, 1),
     "# Reliability metrics\n\nSAIDI (System Average Interruption Duration Index) = sum over events of (customers interrupted x outage minutes) / total customers served. Planned outages are reported separately from unplanned outages. A critical feeder is a feeder supplying a hospital, water treatment plant, or more than 5,000 customers."),
    ("INC-2026-017", "Incident learning: intermittent authentication failures after certificate rotation", "NSW", "current", date(2026, 5, 22),
     "# Incident learning INC-2026-017\n\nIntermittent authentication failures were seen on SCADA gateways after certificate rotation. Root cause: one gateway held the old intermediate certificate. Fix: stage the new chain on all gateways before rotating the leaf. Detection: alarm on handshake failure rate above 2 percent."),
    ("INC-2026-021", "Incident learning: relay mis-operation during storm", "QLD", "current", date(2026, 8, 3),
     "# Incident learning INC-2026-021\n\nA protection relay mis-operated during a storm because of a stale setting group. Fix: verify setting group after every firmware upgrade."),
    ("PRC-SWITCH-050", "Switching of pole-top switches", "SA", "current", date(2026, 7, 9),
     "# Pole-top switch operation (South Australia)\n\nOperate only on instruction from the control room. Confirm remote indication before local operation. After operation, report status to the control room within 10 minutes."),
    ("STD-EARTH-060", "Earthing standard", "ALL", "draft", date(2026, 9, 30),
     "# Earthing standard [DRAFT — not approved]\n\nProposed new earth resistance limit of 5 ohms. Not yet in force."),
    ("PRC-CREW-070", "Crew dispatch rules", "ALL", "current", date(2026, 4, 2),
     "# Crew dispatch\n\nHV switching work requires a crew with the HV_switching skill. A crew is available only if marked available for the work date. Never dispatch a crew for a P3 job when a P1 or P2 job is waiting in the same region."),
]


def build_documents() -> list[dict]:
    return [{"document_id": d[0], "title": d[1], "region_code": d[2], "status": d[3],
             "effective_date": d[4], "text": d[5]} for d in _DOCS]


# ---------------------------------------------------------------- entry point
def generate() -> dict[str, list[dict]]:
    rng = _rng()
    assets = build_assets(rng)
    outages = build_outages(rng, assets)
    crews, avail = build_crews(rng)
    return {
        "gold_asset_health": assets,
        "gold_outage_events": outages,
        "gold_work_orders": build_work_orders(rng, assets),
        "gold_crews": crews,
        "gold_crew_availability": avail,
        "raw_outage_events": messy_raw_outages(rng, outages),
        "derived_outage_rollup_v1": derived_rollup(outages),
        "draft_outage_summary_wip": draft_summary(outages),
        "raw_inspection_export": raw_inspection_export(rng, assets),
        "procedure_documents": build_documents(),
    }


def expected_answers(tables: dict[str, list[dict]]) -> dict:
    """Ground truth used by Lab 2/6 gold sets. Computed, not typed, so it can never drift."""
    outages = tables["gold_outage_events"]
    assets = {a["asset_id"]: a for a in tables["gold_asset_health"]}
    total_cust = 1_000_000
    p2_vic_oct = sum(1 for o in outages if o["region_code"] == "VIC" and o["priority_code"] == "P2"
                     and o["event_start_ts"].strftime("%Y-%m") == "2026-09")
    unplanned = [o for o in outages if not o["is_planned"]]
    saidi = sum(o["customers_interrupted"] * (o["event_end_ts"] - o["event_start_ts"]).total_seconds() / 60
                for o in unplanned) / total_cust
    return {"p2_vic_2026_09": p2_vic_oct, "saidi_unplanned_minutes_per_1m_customers": round(saidi, 3),
            "critical_feeders": sum(1 for a in assets.values() if a["is_critical_feeder"]),
            "work_order_1042_status": next(w["status"] for w in tables["gold_work_orders"]
                                           if w["work_order_id"] == 1042)}


if __name__ == "__main__":
    t = generate()
    for k, v in t.items():
        print(f"{k:28s} {len(v):6d} rows")
    print(expected_answers(t))
