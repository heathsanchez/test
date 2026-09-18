#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTRACT = ROOT / "contract.json"
LEDGER = ROOT / "ledger.json"
PRESENT = ROOT / "compiled_present.json"


def load(path: Path):
    return json.loads(path.read_text())


def compile_present(contract: dict, ledger: dict) -> dict:
    events = ledger["events"]

    promotions = sorted(
        (
            e for e in events
            if e["type"] == "PROMOTE" and e["status"] == "VERIFIED_LOCAL_CHAMPION"
        ),
        key=lambda e: e["target"],
    )

    active_champions = {}
    for e in promotions:
        target = e["target"]
        if target in active_champions:
            raise RuntimeError(f"conflicting active champion for {target}")
        active_champions[target] = {
            "capability_id": e["id"],
            "source_ledger_event": e["id"],
            "branch": e["candidate"]["branch"],
            "commit": e["candidate"]["commit"],
            "representation": e["candidate"]["representation"],
            "status": e["status"],
            "official_pmu_measured": bool(e.get("evidence", {}).get("official_pmu_measured")),
        }

    reserve_hypotheses = [
        {
            "id": e["id"],
            "source_evidence": e.get("parents", []),
            "state": e["status"],
            "hypothesis": e["hypothesis"],
            "next_calibration": e["next_calibration"],
        }
        for e in sorted((e for e in events if e["type"] == "RESERVE"), key=lambda e: e["id"])
    ]

    active_transitions = sorted(
        e["id"] for e in events
        if e["type"] == "PROPOSE" and e["status"] == "ACTIVE_VERIFICATION"
    )
    revoked = sorted(e["id"] for e in events if e["type"] == "REVOKE")

    return {
        "schema": "qckn-lkc-compiled-present-v1",
        "domain_id": ledger["domain_id"],
        "active_champions": active_champions,
        "reserve_hypotheses": reserve_hypotheses,
        "active_transitions": active_transitions,
        "revoked": revoked,
        "policy": {
            "discovery_replay": "Do not replay discovery merely to regain an already verified problem-local champion.",
            "transfer": "Cross-problem lessons remain RESERVE until independently verified on the target contract.",
            "promotion_gate": contract["gamma"]["promotion_gate"],
        },
    }


def canonical_text(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=False) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    contract = load(CONTRACT)
    ledger = load(LEDGER)
    compiled = compile_present(contract, ledger)
    text = canonical_text(compiled)

    if args.check:
        existing = PRESENT.read_text()
        if existing != text:
            raise SystemExit(
                "compiled_present.json is stale: run qckn_lkc/compile_present.py and commit the result"
            )
        reparsed = json.loads(existing)
        if canonical_text(reparsed) != existing:
            raise SystemExit("compiled present fails exact canonical JSON restart")
        print("PASS_QCKN_LKC_COMPILED_PRESENT")
    else:
        PRESENT.write_text(text)
        print(f"wrote {PRESENT}")


if __name__ == "__main__":
    main()
