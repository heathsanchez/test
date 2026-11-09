"""Source-qualified, observation-only Lean/Nucleus axiom boundary replay."""

import hashlib
import json
import pathlib
import re
import subprocess
import sys

from axiom_dependencies import trace_axioms


EXPECTED = {
    "NorthStar.dependent": ["NorthStar.P", "NorthStar.Q", "NorthStar.givenQ", "NorthStar.implication"],
    "NorthStar.borrowed": ["NorthStar.P", "NorthStar.Q", "NorthStar.givenQ", "NorthStar.implication"],
    "NorthStar.independent": [],
}


def lean_axioms(log: str, theorem: str) -> list[str]:
    escaped = re.escape(theorem)
    absent = re.search(rf"'{escaped}' does not depend on any axioms", log)
    if absent:
        return []
    present = re.search(rf"'{escaped}' depends on axioms: \[([^\]]*)\]", log)
    if present:
        return sorted(x.strip() for x in present.group(1).split(",") if x.strip())
    raise AssertionError(f"Lean did not report an axiom set for {theorem}")


def remove_named_axiom(source: bytes, name_to_remove: str) -> bytes:
    names = {0: ""}
    out = []
    removed = False
    for raw in source.splitlines(keepends=True):
        row = json.loads(raw)
        if "in" in row:
            node = row.get("str", row.get("num"))
            pre = node["pre"]
            names[row["in"]] = names[pre] + ("." if pre else "") + str(node.get("str", node.get("i")))
        if "axiom" in row and names[row["axiom"]["name"]] == name_to_remove:
            removed = True
            continue
        out.append(raw)
    assert removed, f"axiom {name_to_remove} not found in source"
    return b"".join(out)


def main(source_path: str, lean_log_path: str, nucleus_binary: str, report_path: str) -> None:
    raw = pathlib.Path(source_path).read_bytes()
    lean_log = pathlib.Path(lean_log_path).read_text()
    report = {
        "schema": "nucleus-north-star-authentic-axiom-boundary-v1",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "source_generated_by_lean4export": "requires workflow provenance; not implied by bytes",
        "source_theorems": {},
        "nucleus": {},
        "external_intent_authorization": "UNKNOWN",
    }
    try:
        for name, expected in EXPECTED.items():
            source_trace = trace_axioms(raw, name)
            reference = lean_axioms(lean_log, name)
            report["source_theorems"][name] = {
                "independent_source_inventory": source_trace,
                "reference_lean_axioms": reference,
                "agreed": source_trace["status"] == "BOUNDED"
                and source_trace["explicit_axioms"] == expected
                and reference == expected,
            }
        assert all(row["agreed"] for row in report["source_theorems"].values()), report["source_theorems"]

        checker = subprocess.run([nucleus_binary], input=raw, capture_output=True, timeout=90)
        report["nucleus"]["original_exit"] = checker.returncode
        report["nucleus"]["original_stderr_tail"] = checker.stderr.decode(errors="replace").splitlines()[-12:]
        assert checker.returncode == 0, report["nucleus"]

        mutated = remove_named_axiom(raw, "NorthStar.givenQ")
        mutated_trace = trace_axioms(mutated, "NorthStar.dependent")
        altered = subprocess.run([nucleus_binary], input=mutated, capture_output=True, timeout=90)
        report["nucleus"]["removed_axiom_exit"] = altered.returncode
        report["nucleus"]["removed_axiom_sha256"] = hashlib.sha256(mutated).hexdigest()
        report["nucleus"]["removed_axiom_trace"] = mutated_trace
        assert altered.returncode != 0
        assert mutated_trace["status"] == "UNKNOWN"

        source_with_blank_line = raw + b"\n"
        report["changed_source_sha256"] = hashlib.sha256(source_with_blank_line).hexdigest()
        assert report["changed_source_sha256"] != report["source_sha256"]

        report["status"] = "BOUNDED_AUTHENTIC_SOURCE_REPLAY"
    except Exception as exc:
        report["status"] = "UNKNOWN"
        report["failure"] = str(exc)
        raise
    finally:
        pathlib.Path(report_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main(*sys.argv[1:])
