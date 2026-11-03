"""Matched real-Rust Nucleus source-revision controls, no cached proof verdicts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from semantic_inventory import InventoryError, compare, inventory


PINNED_FIXTURE_SHA256 = "5e4664a6d4f05afbeff4e0af19681e88b2817c48787a9a281c4ba95d80483333"
RUN_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
EXPECTED_EXIT = {
    "original": 0,
    "later_rename": 0,
    "renumber_name_id": 0,
    "earlier_binder_change": 0,
    "first_theorem_to_axiom": 0,
    "self_const_forgery": 1,
    "global_quotient_forgery": 1,
}


def _encode(rows):
    return b"".join(json.dumps(row, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode() + b"\n" for row in rows)


def generate_cases(original: bytes):
    """Seven revisions; no mutation silently edits another original input."""
    if hashlib.sha256(original).hexdigest() != PINNED_FIXTURE_SHA256:
        raise ValueError("not the exact independently accepted Nucleus source")
    yield "original", original
    yield "later_rename", original.replace(
        b'"str":"thmProof"', b'"str":"thmProofChanged"')

    rows = [json.loads(line) for line in original.splitlines()]
    renumbered = json.loads(json.dumps(rows))
    for record in renumbered:
        if record.get("in") == 4:
            record["in"] = 44
        if "thm" in record and record["thm"]["name"] == 4:
            record["thm"]["name"] = 44
            record["thm"]["all"] = [44]
    yield "renumber_name_id", _encode(renumbered)

    binder = json.loads(json.dumps(rows))
    for record in binder:
        if record.get("ie") == 5:
            record["lam"]["name"] = 2
    yield "earlier_binder_change", _encode(binder)

    axiom = json.loads(json.dumps(rows))
    for record in axiom:
        if "thm" in record and record["thm"]["name"] == 1:
            record["axiom"] = {"name": 1, "levelParams": [], "type": 4}
            del record["thm"]
    yield "first_theorem_to_axiom", _encode(axiom)

    forged = json.loads(json.dumps(rows))
    for record in forged:
        if record.get("ie") == 11:
            record["const"]["name"] = 4
    yield "self_const_forgery", _encode(forged)

    suffix = original + (b'{"in":10,"str":{"pre":0,"str":"NotQuot"}}\n'
                         b'{"quot":{"kind":"type","levelParams":[],"name":10,"type":0}}\n')
    yield "global_quotient_forgery", suffix


def _run(binary: Path, source: bytes, args=()):
    result = subprocess.run([str(binary), *args], input=source,
                            capture_output=True, env=RUN_ENV, timeout=30, check=False)
    if result.returncode not in (0, 1, 2) or result.stdout:
        raise ValueError("unrecognized Nucleus exit or stdout")
    return {"exit_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            "stderr": result.stderr.decode("utf-8", "strict").strip()}


def qualify(binary: Path, fixture: Path, working_directory: Path):
    binary, fixture = Path(binary).resolve(strict=True), Path(fixture).resolve(strict=True)
    if not binary.is_file() or binary.is_symlink() or not 0 < binary.stat().st_size < 20 << 20:
        raise ValueError("invalid Nucleus executable path")
    with binary.open("rb") as handle:
        if handle.read(4) != b"\x7fELF":
            raise ValueError("not the independent Nucleus Linux binary")
    if not fixture.is_file() or fixture.is_symlink():
        raise ValueError("invalid source fixture")
    original = fixture.read_bytes()
    if hashlib.sha256(original).hexdigest() != PINNED_FIXTURE_SHA256:
        raise ValueError("Nucleus fixture source identity drift")
    working_directory.mkdir(exist_ok=True, parents=True)
    store = working_directory / "mgso-original"
    cases = list(generate_cases(original))
    baseline_inventory = inventory(original)
    arms = []
    for name, source in cases:
        # First invocation runs Nucleus *fresh* and emits its genuine receipts;
        # subsequent source arms always invoke the independent ordinary checker.
        arguments = ("--mgso-shadow-dir", str(store)) if name == "original" else ()
        outcome = _run(binary, source, arguments)
        if outcome["exit_code"] != EXPECTED_EXIT[name]:
            raise ValueError(f"native Nucleus verdict unexpectedly changed in {name}: "
                             f"{outcome['exit_code']}, stderr={outcome['stderr'][:200]}")
        try:
            candidate = compare(original, source)
            status = "CANDIDATE_ONLY"
            refusal = None
        except InventoryError as err:
            candidate = None
            status = "UNKNOWN"
            refusal = str(err)
        arms.append({
            "case": name,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "exit_code": outcome["exit_code"],
            "stderr_sha256": outcome["stderr_sha256"],
            "source_verified_by": "Nucleus",
            "inventory_status": status,
            "inventory_refusal": refusal,
            "candidate_reuse_count": candidate["candidate_reuse_count"] if candidate else 0,
            "candidate_reuse_names": candidate["candidate_reuse_names"] if candidate else [],
            "proof_skips": 0,
            "verification_reuse_authority": "NONE",
        })
    if not (store / "root.json").is_file():
        raise ValueError("fresh accepted Nucleus did not emit canonical MGSO root")
    inspection = {}
    for name, source in cases:
        if name in ("original", "later_rename"):
            result = _run(binary, source, ("--mgso-inspect-dir", str(store)))
            if result["exit_code"] != 2 or "authority=none" not in result["stderr"]:
                raise ValueError("Nucleus inspector acquired proof authority")
            inspection[name] = result
    if "candidate-match" not in inspection["original"]["stderr"]:
        raise ValueError("native original receipt mismatch")
    if "status=stale" not in inspection["later_rename"]["stderr"]:
        raise ValueError("native prior receipt did not invalidate changed export")
    return {
        "type": "nucleus.dependency-native-qualification.v1",
        "authority": "NONE", "complete_kernel_dependency_closure": "UNKNOWN",
        "source_pin": PINNED_FIXTURE_SHA256,
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "original_declarations": len(baseline_inventory["declarations"]),
        "live_kernel_invocations": len(arms), "inspection_only_invocations": len(inspection),
        "proof_skips": 0, "arms": arms,
        "historical_inspection": inspection,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.binary, args.fixture, args.work)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"arms": len(result["arms"]),
                      "native_kernel_invocations": result["live_kernel_invocations"],
                      "inspections_only": result["inspection_only_invocations"],
                      "verdicts": {arm["case"]: arm["exit_code"] for arm in result["arms"]},
                      "proof_skips": 0, "authority": "NONE"}, sort_keys=True))


if __name__ == "__main__":
    main()
