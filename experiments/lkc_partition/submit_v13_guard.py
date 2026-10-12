#!/usr/bin/env python3
"""Fail-closed, one-problem SAIR formal release of already-qualified Partition V13.

Requires a separate successful local verifier and paired cost gate in CI.
Does not mutate the retained eight-problem source portfolio.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/lkc_partition/generated/Submission_v13.lean"
OUT = ROOT / "lkc-partition-v13-release-receipt.json"
BASE = "https://api.sair.foundation/api/public/v1/competitions/lean-kernel-challenge"
EXPECTED_SOURCE_SHA256 = "bcb6325b9d0ca5c7259b0de76d903ba5cb20e05fdb60938b5201745d00491085"
EXPECTED_CONTRACT = "ddd9cae8db44a2ace1adea86e908263087aae499"
EXPECTED_PRIOR_SUBMISSION = "388"
PROBLEM = "partition"


def call(method: str, suffix: str, payload: object | None = None) -> dict:
    token = os.environ.get("SAIR_API_KEY")
    if not token:
        raise RuntimeError("SAIR_API_KEY unavailable: no submission made")
    command = [
        "curl", "-fsS", "--retry", "2", "--connect-timeout", "20",
        "--max-time", "120", "-X", method, BASE + suffix,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Accept: application/json", "-H", "User-Agent: curl/8.5.0",
    ]
    input_data = None
    if payload is not None:
        command.extend(["-H", "Content-Type: application/json", "--data-binary", "@-"])
        input_data = json.dumps(payload)
    proc = subprocess.run(command, input=input_data, capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"{method} {suffix} failed (exit {proc.returncode}); no retry POST")
    obj = json.loads(proc.stdout)
    if not obj.get("ok"):
        raise RuntimeError(f"{method} {suffix} API returned non-ok; no success inferred")
    return obj


def main() -> None:
    if os.environ.get("LKC_VERIFIED_COST_GATE") != "PASS":
        raise RuntimeError("Independent source/Lean/cost gate absent: refusing POST")
    if not SOURCE.is_file():
        raise RuntimeError("Generated candidate missing")
    content = SOURCE.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    if sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Source hash mismatch: {sha}")
    if len(content) > 1048576:
        raise RuntimeError("Source exceeds 1MiB")
    info = call("GET", "/me")["data"]
    if info.get("team", {}).get("teamNumber") != "LKC01-T00023":
        raise RuntimeError("Unexpected SAIR team identity")
    if not info.get("canSubmit"):
        raise RuntimeError("SAIR says submission unavailable")
    spec = call("GET", "/submission-spec")["data"]
    contract = spec.get("contractVersion")
    if contract != EXPECTED_CONTRACT:
        raise RuntimeError(f"Evaluator contract changed: {contract}. Requalify before POST.")
    mine = call("GET", "/submissions/mine?limit=100")["data"]["items"]
    existing = [x for x in mine if x.get("problem") == PROBLEM]
    if len(existing) != 1 or str(existing[0].get("submissionId")) != EXPECTED_PRIOR_SUBMISSION:
        raise RuntimeError("Current selected Partition submission differs from frozen #388; refusing to overwrite")
    current = existing[0]
    daily = current.get("dailyEvaluation", {})
    if daily.get("status") != "accepted" or not daily.get("replayReport", {}).get("eligible"):
        raise RuntimeError("Prior official Partition entry not certified accepted")
    idem = str(uuid.uuid5(uuid.NAMESPACE_URL,
                          f"{BASE}/submissions|{contract}|{PROBLEM}|{sha}"))
    payload = {
        "idempotencyKey": idem,
        "contractVersionAcknowledged": contract,
        "payload": {"problem": PROBLEM, "text": content.decode("utf-8")}
    }
    response = call("POST", "/submissions", payload)
    receipt = {
        "problem": PROBLEM,
        "replaces": EXPECTED_PRIOR_SUBMISSION,
        "sourceSha256": sha,
        "contractVersion": contract,
        "idempotencyKey": idem,
        "response": response,
        "note": "POST accepted by API is not an official evaluation or rank."
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print("SAIR_PARTITION_V13_FORMAL_SUBMISSION_CREATED")
    print(json.dumps({k: receipt[k] for k in ("problem", "replaces", "sourceSha256", "contractVersion")}))
    print(json.dumps(response))


if __name__ == "__main__":
    main()
