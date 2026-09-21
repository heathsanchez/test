#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, uuid, urllib.request, urllib.error
from pathlib import Path

BASE = "https://api.sair.foundation/api/public/v1/competitions/lean-kernel-challenge"
ROOT = Path(__file__).resolve().parent / "official_submissions"
PROBLEMS = [
    "ca-rule110",
    "fib",
    "mertens",
    "partition",
    "polydisc",
    "primecount",
    "permanent",
    "sha256",
]

API_KEY = os.environ.get("SAIR_API_KEY")
if not API_KEY:
    raise SystemExit("SAIR_API_KEY is not set")

def request(method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise SystemExit(f"{method} {path} -> HTTP {e.code}\n{body}")

def contract_version():
    obj = request("GET", "/submission-spec")
    try:
        return obj["data"]["contractVersion"]
    except Exception:
        raise SystemExit("submission-spec response missing data.contractVersion:\n" + json.dumps(obj, indent=2))

def submit(problem: str):
    source_path = ROOT / problem / "Submission.lean"
    if not source_path.exists():
        raise SystemExit(f"missing {source_path}")
    contract = contract_version()
    payload = {
        "idempotencyKey": str(uuid.uuid4()),
        "contractVersionAcknowledged": contract,
        "payload": {
            "problem": problem,
            "text": source_path.read_text(),
        },
    }
    obj = request("POST", "/submissions", payload)
    return obj

def main():
    out = {"submitted": [], "mine": None}
    for problem in PROBLEMS:
        print(f"Submitting {problem}...", flush=True)
        obj = submit(problem)
        out["submitted"].append({"problem": problem, "response": obj})
        print(json.dumps(obj, indent=2), flush=True)

    print("Reviewing team submissions...", flush=True)
    mine = request("GET", "/submissions/mine?limit=50")
    out["mine"] = mine
    Path("sair-submission-receipts.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(mine, indent=2))

if __name__ == "__main__":
    main()
