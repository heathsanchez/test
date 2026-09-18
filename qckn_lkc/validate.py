#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = "https://github.com/heathsanchez/test.git"
OFFICIAL = "https://github.com/SAIRcompetition/lean-kernel-challenge.git"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load(name: str):
    return json.loads((ROOT / name).read_text())


def fail(message: str):
    raise SystemExit(message)


def check_dag(events: list[dict]):
    by_id = {e["id"]: e for e in events}
    if len(by_id) != len(events):
        fail("duplicate ledger event id")

    for e in events:
        for p in e.get("parents", []):
            if p not in by_id:
                fail(f"{e['id']}: missing parent {p}")

    visiting = set()
    done = set()

    def visit(event_id: str):
        if event_id in done:
            return
        if event_id in visiting:
            fail(f"causal cycle at {event_id}")
        visiting.add(event_id)
        for p in by_id[event_id].get("parents", []):
            visit(p)
        visiting.remove(event_id)
        done.add(event_id)

    for event_id in by_id:
        visit(event_id)
    return by_id


def ls_remote(url: str, branch: str) -> str:
    result = subprocess.run(
        ["git", "ls-remote", url, f"refs/heads/{branch}"],
        check=True,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if not result.stdout.strip():
        fail(f"missing remote branch: {branch}")
    return result.stdout.split()[0]


def verify_refs(by_id: dict[str, dict], present: dict):
    checked = []

    refs = []
    for target, champion in present["active_champions"].items():
        refs.append((f"champion:{target}", champion["branch"], champion["commit"]))

    for event_id in present["active_transitions"]:
        event = by_id[event_id]
        candidate = event.get("candidate", {})
        branch = candidate.get("branch")
        commit = candidate.get("commit")
        if branch and commit:
            refs.append((event_id, branch, commit))

    for identity, branch, commit in refs:
        if not HEX40.fullmatch(commit):
            fail(f"{identity}: invalid commit digest")
        actual = ls_remote(REPO, branch)
        if actual != commit:
            fail(f"{identity}: stale active branch snapshot {branch}: expected {commit}, got {actual}")
        checked.append((branch, commit))

    print(f"verified {len(checked)} active/frozen branch snapshots")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-refs", action="store_true")
    parser.add_argument("--verify-rules-head", action="store_true")
    args = parser.parse_args()

    contract = load("contract.json")
    ledger = load("ledger.json")
    present = load("compiled_present.json")

    if contract["domain_id"] != ledger["domain_id"] or ledger["domain_id"] != present["domain_id"]:
        fail("domain id mismatch")

    if contract["qckn_profile"] != "domain-adapter":
        fail("competition adapter must not claim the QCK theorem surface")

    events = ledger["events"]
    by_id = check_dag(events)

    required_gate_terms = {
        "universal proof",
        "axiom/restriction audit",
        "canonical acceptance",
        "same-byte hash binding",
        "paired resource measurement against protected champion",
        "strict resource improvement for local promotion",
    }
    gate = set(contract["gamma"]["promotion_gate"])
    if not required_gate_terms <= gate:
        fail("promotion gate is weaker than the declared competition contract")

    promotions_by_target = {}
    for e in events:
        if e["type"] == "PROMOTE" and e["status"] == "VERIFIED_LOCAL_CHAMPION":
            promotions_by_target[e["target"]] = e

    for target, champion in present["active_champions"].items():
        event_id = champion["source_ledger_event"]
        if event_id not in by_id:
            fail(f"{target}: champion event missing")
        event = by_id[event_id]
        if event["type"] != "PROMOTE" or event["status"] != "VERIFIED_LOCAL_CHAMPION":
            fail(f"{target}: unearned champion in compiled present")
        if promotions_by_target.get(target, {}).get("id") != event_id:
            fail(f"{target}: compiled champion is not latest causal promotion")
        if event["candidate"]["commit"] != champion["commit"]:
            fail(f"{target}: champion commit mismatch")

    for event_id in present["active_transitions"]:
        event = by_id.get(event_id)
        if not event or event["type"] != "PROPOSE" or event["status"] != "ACTIVE_VERIFICATION":
            fail(f"{event_id}: invalid active transition")

    for event_id in present["revoked"]:
        event = by_id.get(event_id)
        if not event or event["type"] != "REVOKE":
            fail(f"{event_id}: invalid revocation")

    for h in present["reserve_hypotheses"]:
        event = by_id.get(h["id"])
        if not event or event["type"] != "RESERVE":
            fail(f"{h['id']}: reserve item is not ledger-backed")
        if event["status"].startswith("VERIFIED"):
            fail(f"{h['id']}: reserve hypothesis incorrectly promoted")

    resolved = {
        parent
        for e in events
        if e["type"] == "RESOLVE"
        for parent in e.get("parents", [])
    }
    if any(event_id in resolved for event_id in present["active_transitions"]):
        fail("resolved transition remains active in compiled present")

    if args.verify_refs:
        verify_refs(by_id, present)

    if args.verify_rules_head:
        expected = contract["gamma"]["environment"]["rules_commit"]
        actual = ls_remote(OFFICIAL, "main")
        if actual != expected:
            fail(f"official rules head drifted: expected {expected}, got {actual}")
        print("official rules head matches declared contract")

    print("PASS_QCKN_LKC_DOMAIN_VALIDATION")


if __name__ == "__main__":
    main()
