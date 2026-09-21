#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent
ROOT = REPO / "official_submissions"
RECEIPTS = REPO / "sair-submission-receipts.json"
BASE = "https://api.sair.foundation/api/public/v1/competitions/lean-kernel-challenge"

PROBLEMS = [
    "ca-rule110", "fib", "mertens", "partition",
    "polydisc", "primecount", "permanent", "sha256",
]

EXPECTED = {
    "ca-rule110": "ba0074747e59c898d448bea8d0995dc8c9809ca857791db97ca3cb35c44909a9",
    "fib": "ecacca9af5c87a4ed66c573131ff9f542a8f5ab1b9b3f0e9a6753f1360dd6cde",
    "mertens": "b9f57508d255d018209e66d1274a12fdff9a44d5b996bc39679de72e0d8f92c7",
    "partition": "2a191971ed624b45342a8bdf325887b5c6553fe5ce67f97c719bb239cd2a08b0",
    "polydisc": "8c029f22112ecd7fffd6c73f65ec499e7794dab26892a434c85fa63df6b7f6d0",
    "primecount": "9ac8ac20e740f1ffa7d4b8b55816a2f25e2e51331cbd5d0181304fc35178fffa",
    "permanent": "7901b6bcd8aa87a82322b4ee0e697c6c193c9354d4b04481be611b9bed40ce39",
    "sha256": "07ba4769dc8fc218556890286947db89a19b6f8110b110d494c6e3b24e618204",
}

GENERATORS = {
    "ca-rule110": (
        [
            "experiments/lkc_rule110/payload_mask_v51.py",
            "experiments/lkc_rule110/init_bias_v52.py",
            "experiments/lkc_rule110/mod_gather_v54.py",
            "experiments/lkc_rule110/maskless_bstep_v58.py",
            "experiments/lkc_rule110/fix_v58_chain.py",
            "experiments/lkc_rule110/ast_fusion_v60.py",
        ],
        "experiments/lkc_rule110/generated/Submission_v60.lean",
    ),
    "fib": (
        ["experiments/lkc_fib/bitwise_v2.py"],
        "experiments/lkc_fib/generated/Submission_v2.lean",
    ),
    "mertens": (
        ["experiments/lkc_mertens/structural_v6.py"],
        "experiments/lkc_mertens/generated/Submission_v6.lean",
    ),
    "partition": (
        ["experiments/lkc_partition/rowdp_v4.py"],
        "experiments/lkc_partition/generated/Submission_v4.lean",
    ),
    "polydisc": (
        ["experiments/lkc_polydisc/shift_v3.py"],
        "experiments/lkc_polydisc/generated/Submission_v3.lean",
    ),
    "primecount": (
        ["experiments/lkc_primecount/structural_v3.py"],
        "experiments/lkc_primecount/generated/Submission_v3.lean",
    ),
    "permanent": (
        ["experiments/lkc_permanent/full_v5.py"],
        "experiments/lkc_permanent/generated/Submission_v5.lean",
    ),
    "sha256": (
        ["experiments/lkc_sha256/algebra_fullproof_v21.py"],
        "experiments/lkc_sha256/generated/Submission_algebra_v21_proof.lean",
    ),
}

API_KEY = os.environ.get("SAIR_API_KEY")
if not API_KEY:
    raise SystemExit("SAIR_API_KEY is not set")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_exact_files() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for problem in PROBLEMS:
        scripts, output = GENERATORS[problem]
        for rel in scripts:
            p = REPO / rel
            if not p.exists():
                raise SystemExit(f"{problem}: missing generator {rel}")
            subprocess.run([sys.executable, str(p)], cwd=REPO, check=True)

        generated = REPO / output
        if not generated.exists():
            raise SystemExit(f"{problem}: missing generated file {output}")

        got = digest(generated)
        want = EXPECTED[problem]
        if got != want:
            raise SystemExit(
                f"{problem}: frozen hash mismatch; refusing submission\n"
                f"got  {got}\nwant {want}"
            )

        outdir = ROOT / problem
        outdir.mkdir(parents=True, exist_ok=True)
        dest = outdir / "Submission.lean"
        shutil.copyfile(generated, dest)
        print(f"READY {problem} {got} {dest.stat().st_size} bytes", flush=True)


def request(method: str, path: str, payload=None):
    url = BASE + path
    cmd = [
        "curl", "-sS",
        "--connect-timeout", "30",
        "--max-time", "120",
        "-X", method,
        url,
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Accept: application/json",
        "-H", "User-Agent: curl/8.5.0",
        "-w", "\n%{http_code}",
    ]
    body = None
    if payload is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
        body = json.dumps(payload)

    proc = subprocess.run(
        cmd,
        input=body,
        text=True,
        capture_output=True,
        cwd=REPO,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{method} {path} curl failed ({proc.returncode}): {proc.stderr.strip()}"
        )

    raw = proc.stdout
    if "\n" not in raw:
        raise RuntimeError(f"{method} {path}: malformed curl response")
    text_body, status = raw.rsplit("\n", 1)
    if not status.isdigit():
        raise RuntimeError(f"{method} {path}: malformed HTTP status {status!r}")
    code = int(status)
    if code < 200 or code >= 300:
        raise RuntimeError(f"{method} {path} -> HTTP {code}\n{text_body}")
    try:
        return json.loads(text_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{method} {path}: non-JSON success response\n{text_body[:4000]}"
        ) from exc


def contract_version() -> str:
    obj = request("GET", "/submission-spec")
    try:
        return obj["data"]["contractVersion"]
    except Exception as exc:
        raise RuntimeError(
            "submission-spec response missing data.contractVersion:\n"
            + json.dumps(obj, indent=2)
        ) from exc


def save(out: dict) -> None:
    RECEIPTS.write_text(json.dumps(out, indent=2) + "\n")


def submit(problem: str):
    source = ROOT / problem / "Submission.lean"
    contract = contract_version()
    source_hash = digest(source)

    # Stable retry key for these exact bytes under this exact contract.
    idem = str(uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"{BASE}/submissions|{contract}|{problem}|{source_hash}",
    ))

    payload = {
        "idempotencyKey": idem,
        "contractVersionAcknowledged": contract,
        "payload": {
            "problem": problem,
            "text": source.read_text(),
        },
    }
    return contract, idem, request("POST", "/submissions", payload)


def main() -> None:
    prepare_exact_files()
    out = {"submitted": [], "mine": None}
    save(out)

    for problem in PROBLEMS:
        print(f"Submitting {problem}...", flush=True)
        contract, idem, response = submit(problem)
        record = {
            "problem": problem,
            "contractVersionAcknowledged": contract,
            "idempotencyKey": idem,
            "response": response,
        }
        out["submitted"].append(record)
        save(out)
        print(json.dumps(record, indent=2), flush=True)

    print("Reviewing team submissions...", flush=True)
    out["mine"] = request("GET", "/submissions/mine?limit=50")
    save(out)
    print(json.dumps(out["mine"], indent=2), flush=True)


if __name__ == "__main__":
    main()
