#!/usr/bin/env python3
"""Replay exact upstream VDN plus the generated bounded V54 certificate.

No Lean dependency manager or downloaded library is needed. The compiler is
supplied separately and must be the original project's exact toolchain version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE.parent / "archaeology/formal/mathgraph-source"
UPSTREAM = {
    "VerifiedDevelopmentalNavigation.lean": "3e59e939fdef904d5b5d0b367a7c916b5b422990e06630f86d8bd3c2c5d5ac1b",
    "DevelopmentCertificate.lean": "fc266183da8d7de2e5bc82b9eea093b64719fd9ef8f90f7c14e5bb3fe9b98a0a",
    "Routing.lean": "cb3bb5cf6a4cdc013da787d98bc50d35aa4d74d2087632fb73283efcaa24da6c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate", type=Path, default=HERE / "GeneratedV54.lean")
    parser.add_argument("--output-dir", type=Path, default=HERE / ".build")
    parser.add_argument("--receipt", type=Path,
                        help="Reviewable receipt (default: beside certificate as lean-verification.json)")
    parser.add_argument("--lean", default=os.environ.get("V54_LEAN", "lean"))
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "v54-lean-check-v1", "status": "UNKNOWN",
        "upstream_commit": "cf359686c74549a132c7a651cd7aabc7c1a870fe",
        "toolchain": "leanprover/lean4:v4.28.0", "commands": [],
        "scope": "Exact source-hash transition table and old trace length <= 1; no Python refinement theorem.",
    }
    receipt_path = out / "verification.json"
    reviewable = args.receipt or args.certificate.resolve().parent / "lean-verification.json"
    reviewable.parent.mkdir(parents=True, exist_ok=True)
    reviewable.write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        compiler = shutil.which(args.lean)
        if compiler is None:
            raise ValueError(f"Lean compiler unavailable: {args.lean}")
        version = subprocess.run([compiler, "--version"], check=True, text=True,
                                 capture_output=True, timeout=15).stdout.strip()
        receipt["compiler_version"] = version
        if not re.search(r"version 4\.28\.0(?:,|\))", version):
            raise ValueError("Compiler does not match exact original Lean v4.28.0")
        for name, expected in UPSTREAM.items():
            actual = sha256(SOURCE_ROOT / name)
            if actual != expected:
                raise ValueError(f"Original upstream file changed: {name}")
        receipt["upstream_source_sha256"] = UPSTREAM
        certificate = args.certificate.resolve()
        if not certificate.is_file():
            raise ValueError(f"No concrete generated certificate: {certificate}")
        evidence_path = certificate.parent / "evidence-manifest.json"
        evidence = json.loads(evidence_path.read_text())
        if evidence.get("status") != "EVIDENCE_COMPLETE_AWAITING_LEAN":
            raise ValueError("Concrete native evidence manifest is not complete")
        if evidence.get("generated", {}).get("sha256") != sha256(certificate):
            raise ValueError("Concrete certificate differs from admitted native evidence")
        admitted = {}
        for key, item in {**evidence.get("artifacts", {}), "transition_table": evidence["transition_table"]}.items():
            path = Path(item["path"])
            path = path if path.is_absolute() else evidence_path.parent / path
            if sha256(path) != item["sha256"]:
                raise ValueError(f"Admitted native evidence changed: {item['path']}")
            admitted[key] = path
        # Re-run evidence admission from the frozen inputs, so hashes in a
        # supplied manifest cannot substitute for the generator's checks.
        with tempfile.TemporaryDirectory(prefix="readmission-", dir=out) as directory:
            readmission = Path(directory)
            command = [sys.executable, str(HERE / "generate.py"),
                       "--native-calls", str(admitted["native_calls"]),
                       "--broken", str(admitted["broken"]), "--warm", str(admitted["warm"]),
                       "--final", str(admitted["final"]), "--provenance", str(admitted["provenance"]),
                       "--output-dir", str(readmission)]
            if evidence.get("acquired_operator_identity_checked"):
                command += ["--input", str(admitted["acquisition"])]
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
            if ((readmission / "GeneratedV54.lean").read_bytes() != certificate.read_bytes()
                    or (readmission / "transition-table.json").read_bytes() != admitted["transition_table"].read_bytes()):
                raise ValueError("Concrete certificate/table differs from independent evidence re-admission")
        receipt["evidence_readmission"] = "MATCHED_FROZEN_INPUTS"
        receipt["evidence_manifest_sha256"] = sha256(evidence_path)
        receipt["candidate_count"] = evidence["candidate_count"]
        receipt["cold_outcome_counts"] = evidence["cold_outcome_counts"]
        for proof_source in (certificate, HERE / "BoundedV54.lean"):
            if re.search(r"\b(sorry|admit|axiom|unsafe)\b", proof_source.read_text()):
                raise ValueError(f"Proof source contains a prohibited proof escape: {proof_source.name}")
        receipt["certificate_sha256"] = sha256(certificate)
        receipt["glue_sha256"] = sha256(HERE / "BoundedV54.lean")
        receipt["generator_sha256"] = sha256(HERE / "generate.py")
        build = out / "lib"
        (build / "VerifiedDevelopmentalNavigation").mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["LEAN_PATH"] = str(build)
        steps = [
            (SOURCE_ROOT / "VerifiedDevelopmentalNavigation.lean", build / "VerifiedDevelopmentalNavigation.olean"),
            (SOURCE_ROOT / "DevelopmentCertificate.lean", build / "VerifiedDevelopmentalNavigation/DevelopmentCertificate.olean"),
            (SOURCE_ROOT / "Routing.lean", build / "VerifiedDevelopmentalNavigation/Routing.olean"),
            (HERE / "BoundedV54.lean", build / "BoundedV54.olean"),
            (certificate, build / "GeneratedV54.olean"),
        ]
        logs = []
        for src, olean in steps:
            command = [compiler, "-o", str(olean), str(src)]
            started = time.monotonic()
            run = subprocess.run(command, env=env, text=True, capture_output=True,
                                 timeout=args.timeout)
            log = run.stdout + run.stderr
            logs.append(f"$ {' '.join(command)}\n{log}")
            receipt["commands"].append({"source": src.name, "source_sha256": sha256(src),
                                        "returncode": run.returncode,
                                        "elapsed_seconds": round(time.monotonic() - started, 3)})
            (out / "lean.log").write_text("\n".join(logs))
            if run.returncode:
                raise ValueError(f"Lean rejected {src.name}; see {out / 'lean.log'}")
            if "sorryAx" in log or "declaration uses 'sorry'" in log:
                raise ValueError("Lean output contains sorryAx")
        report = logs[-1].split("\n", 1)[1].strip()
        expected_declarations = {"ActualV54.certifiedPhaseChange", "ActualV54.everyOldCapabilityRetained",
                                 "ActualV54.oldBoundaryHasNoRecordedPass", "ActualV54.finalHasRecordedPass"}
        audits = re.findall(r"'([^']+)' (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", report)
        if {name for name, _ in audits} != expected_declarations:
            raise ValueError("Concrete theorem axiom audit is absent or incomplete")
        allowed = {"propext", "Quot.sound"}
        used = {item.strip() for _, names in audits for item in names.split(",") if item.strip()}
        if not used <= allowed:
            raise ValueError(f"Unexpected proof axioms: {sorted(used - allowed)}")
        receipt["status"] = "CHECKED_BOUNDED_TABLE_CERTIFICATE"
        receipt["axiom_report"] = report
        receipt["allowed_axioms"] = sorted(allowed)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        receipt["reason"] = str(exc)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    reviewable.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path),
                      "reviewable_receipt": str(reviewable),
                      "reason": receipt.get("reason")}, indent=2))
    return 0 if receipt["status"] == "CHECKED_BOUNDED_TABLE_CERTIFICATE" else 1


if __name__ == "__main__":
    sys.exit(main())
