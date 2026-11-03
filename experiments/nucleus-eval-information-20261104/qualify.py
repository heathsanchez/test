"""Qualify two-parameter EvalInformation admission on exact source and controls.

Retains every existing protected Nucleus gate, adding official differential
controls before promoting any candidate or proceeding to complete Mathlib.
"""
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "prior_carrier_qualify", ROOT.parent / "nucleus-nonzero-carrier-20261104/qualify.py"
)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
C, Q = P.C, P.Q
C.OUT = Path("/tmp/nucleus-eval-information-qualified")
EXPECTED_BASELINE = "013e742dc3bf541301235b6e6d37615b62c9800b923b7c9506b254cffdbfe61e"
SOURCE_SHA = "f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4"
REFERENCE_SHA = "ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94"


def eval_gate(binary, env):
    source = Path("/tmp/eval-frontier.ndjson")
    assert Q.t.digest(source) == SOURCE_SHA
    reference = Path("/tmp/k-reference/bundle/kernel")
    assert Q.t.digest(reference) == REFERENCE_SHA
    ancestor = Path("/tmp/eval-ancestor/candidate/nucleus")
    assert Q.t.digest(ancestor) == EXPECTED_BASELINE
    prior = json.loads(Path("/tmp/eval-ancestor/qualification.json").read_text())["candidate"]
    assert prior["qualified"] and prior["binary_sha"] == EXPECTED_BASELINE
    ancestor.chmod(0o755)
    red = Q.t.measure(ancestor, source, env, C.OUT / "red-eval", timeout=180, perf=False)
    assert red["rc"] == 2
    assert "Lean.Data.AC.EvalInformation" in (C.OUT / "red-eval/stderr").read_text()

    fixtures = C.OUT / "eval-fixtures"
    subprocess.run(["python3", str(ROOT / "generate.py"), "--source",
                    str(source), "--out", str(fixtures)], check=True)
    manifest = json.loads((fixtures / "inputs.json").read_text())
    assert len(manifest) == 14
    rows = []
    for entry in manifest:
        fixture = fixtures / entry["file"]
        assert Q.t.digest(fixture) == entry["sha256"]
        stem = C.OUT / "eval-differential" / entry["case"]
        parse_rc = C.captured([str(reference), "--parse-only", str(fixture)],
                              stem / "parse", timeout=180)
        reference_rc = C.captured([str(reference), str(fixture)],
                                  stem / "reference", timeout=180)
        with fixture.open("rb") as stream:
            candidate_rc = C.captured([str(binary)], stem / "candidate",
                                      env=env | {"NUCLEUS_TRACE_GENERIC_NONREC": "1"},
                                      stdin=stream, timeout=180)
        passed = (parse_rc == 0
                  and reference_rc == entry["expect_reference"]
                  and (candidate_rc == 0 if reference_rc == 0 else candidate_rc in (1, 2)))
        row = {**entry, "reference_parse_rc": parse_rc,
               "reference_rc": reference_rc, "candidate_rc": candidate_rc,
               "pass_": passed}
        rows.append(row)
        Q.t.write_json(C.OUT / "eval_gate.json", {
            "candidate_binary_sha": Q.t.digest(binary),
            "reference_binary_sha": REFERENCE_SHA,
            "ancestor_binary_sha": EXPECTED_BASELINE,
            "source_sha": SOURCE_SHA,
            "rows": rows,
            "passed": len(rows) == 14 and all(r["pass_"] for r in rows)
        })
        print("EVAL_INFORMATION_CONTROL", json.dumps(row), flush=True)
        assert passed, "No promotion for unsupported valid input or false ACCEPT"

    # Re-run all 14 with explicit oracle results and unchanged 21 prior
    # adversarial controls before complete Mathlib; no selector-only shortcut.
    P.gate(binary, env)


def main():
    C.OUT.mkdir(exist_ok=True)
    # The original bounded nonzero patch is a fully qualified ancestry; this
    # second patch has only a guarded selector for the existing derivation.
    combined = Path("/tmp/nucleus-eval-composed.patch")
    combined.write_text(
        (ROOT.parent / "nucleus-nonzero-carrier-20261104/combined.patch").read_text()
        + "\n" + (ROOT / "admit-eval.patch").read_text()
    )
    C.main(additional_patch=combined, additional_gate=eval_gate)
    protected = json.loads((C.OUT / "qualification.json").read_text())["candidate"]
    source = json.loads((C.OUT / "full.json").read_text())
    gate = json.loads((C.OUT / "eval_gate.json").read_text())
    assert protected["qualified"] and gate["passed"]
    Q.t.write_json(C.OUT / "eval_qualification.json", {
        "status": "WARRANTED_BOUNDED",
        "source_sha": SOURCE_SHA,
        "adversarial_controls": len(gate["rows"]),
        "retained_nonzero_controls": 14,
        "retained_prior_controls": 21,
        "binary_sha": protected["binary_sha"],
        "source_patch_sha": protected["source_patch_sha"],
        "full": source,
    })


if __name__ == "__main__":
    main()
