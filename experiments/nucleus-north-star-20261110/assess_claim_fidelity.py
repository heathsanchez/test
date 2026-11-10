"""Exact synthetic claim-boundary assessment; never authorizes real intent."""

import hashlib
import json
import pathlib
import subprocess
import sys

from axiom_dependencies import trace_axioms


EXPECTED_CONTRACT = {
    "schema": "nucleus-north-star-synthetic-claim-v1",
    "checked_declaration": "NorthStarClaim.checkedTheorem",
    "checked_type": "∀ (R : Prop), R → R",
    "intended_type": "∀ (R : Prop), R",
    "separation_declaration": "NorthStarClaim.separation",
    "authorization": "SYNTHETIC_CONTROL_ONLY",
}


def require_exact_synthetic_contract(contract: dict) -> None:
    assert contract == EXPECTED_CONTRACT, "Unqualified or altered synthetic contract"


def require_lean_witness(log: str) -> None:
    for declaration in ("NorthStarClaim.checkedTheorem", "NorthStarClaim.separation"):
        sentence = f"'{declaration}' does not depend on any axioms"
        assert any(line.strip() == sentence for line in log.splitlines()), (
            f"Missing exact zero-axiom Lean oracle for {declaration}"
        )


def assess(
    raw_export: bytes,
    lean_log: str,
    contract: dict,
    checker_binary: str,
) -> dict:
    """Combine distinct observations without promoting them to a real intent warrant."""
    require_exact_synthetic_contract(contract)
    require_lean_witness(lean_log)
    inventory = trace_axioms(raw_export, "NorthStarClaim.checkedTheorem")
    assert inventory["status"] == "BOUNDED" and inventory["explicit_axioms"] == [], inventory
    checker = subprocess.run([checker_binary], input=raw_export, capture_output=True, timeout=90)
    assert checker.returncode == 0, checker.stderr.decode(errors="replace")[-2000:]
    return {
        "status": "BOUNDED_SYNTHETIC_CLAIM_SEPARATION",
        "nucleus_verdict": "ACCEPT",
        "source_inventory": inventory,
        "lean_axiom_oracle": "both declarations axiom-free",
        "lean_separation_witness": "NorthStarClaim.separation",
        "checked_proposition": contract["checked_type"],
        "synthetic_intended_proposition": contract["intended_type"],
        "synthetic_claim_fidelity": "REFUTED_BY_LEAN_WITNESS",
        "external_owner_intent": "UNKNOWN",
        "declaration_export_sha256": hashlib.sha256(raw_export).hexdigest(),
        "contract_sha256": hashlib.sha256(
            json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def main(export_path: str, lean_log_path: str, contract_path: str,
         checker_binary: str, report_path: str) -> None:
    report = {"status": "UNKNOWN", "external_owner_intent": "UNKNOWN"}
    try:
        report = assess(
            pathlib.Path(export_path).read_bytes(),
            pathlib.Path(lean_log_path).read_text(),
            json.loads(pathlib.Path(contract_path).read_text()),
            checker_binary,
        )
    except Exception as exc:
        report["failure"] = str(exc)
        raise
    finally:
        pathlib.Path(report_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:])
