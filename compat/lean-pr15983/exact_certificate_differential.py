#!/usr/bin/env python3
"""Exact Lean 15983 export, theorem-type-only coefficient mutant and differential verdicts.

This is a verifier of observable checker outcomes, NOT an authorization to
rewrite Nucleus's kernel rules. Exit 0 only for complete qualified results.
"""
import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

LEAN_COMMIT = "33c050d0430abeb345e27a4e3f6a261e97e15a16"
FORMAT = "3.1.0"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def find_thm(rows):
    names = {0: ""}
    for obj in rows:
        if "in" in obj:
            number = obj["in"]
            if "str" in obj:
                prefix = obj["str"]["pre"]
                suffix = obj["str"]["str"]
            elif "num" in obj:
                prefix = obj["num"]["pre"]
                suffix = str(obj["num"]["i"])
            else:
                continue
            names[number] = names.get(prefix, "") + ("." if prefix else "") + suffix
    found = [(i, o["thm"]) for i, o in enumerate(rows)
             if "thm" in o and names.get(o["thm"]["name"]) == "ex₁"]
    assert len(found) == 1, "exact named ex₁ theorem missing or duplicated"
    return found[0]

def mutant(rows):
    """Copy just a type DAG path to a changed natural literal; leave original proof DAG intact."""
    source_index, theorem = find_thm(rows)
    exprs = {o["ie"]: o for o in rows if "ie" in o}
    next_expr = max(exprs, default=0) + 1
    replacements = []
    changed = False
    fresh = []

    def clone(idx):
        nonlocal next_expr, changed
        old = exprs[idx]
        candidate = copy.deepcopy(old)
        keys = []
        if "app" in old:
            keys = [("app", "fn"), ("app", "arg")]
        elif "forallE" in old:
            keys = [("forallE", "type"), ("forallE", "body")]
        elif "lam" in old:
            keys = [("lam", "type"), ("lam", "body")]
        elif "letE" in old:
            keys = [("letE", "type"), ("letE", "value"), ("letE", "body")]
        elif "proj" in old:
            keys = [("proj", "struct")]
        elif "mdata" in old:
            keys = [("mdata", "expr")]
        changed_here = False
        if not changed and old.get("natVal") == "2":
            candidate["natVal"] = "3"
            changed = changed_here = True
            replacements.append({"old_expr": idx, "before": "2", "after": "3"})
        for tag, field in keys:
            before = old[tag][field]
            after = clone(before)
            if after != before:
                candidate[tag][field] = after
                changed_here = True
        if not changed_here:
            return idx
        candidate["ie"] = next_expr
        next_expr += 1
        fresh.append(candidate)
        return candidate["ie"]

    new_type = clone(theorem["type"])
    assert changed and new_type != theorem["type"], \
        "no numeral 2 on theorem proposition DAG; do not fabricate a mutant"
    updated = copy.deepcopy(rows)
    updated[source_index]["thm"]["type"] = new_type
    assert updated[source_index]["thm"]["value"] == theorem["value"], \
        "proof body changed: this is not a type-only mutation"
    # Expression IDs are emitted before use; insert cloned DAG nodes before the theorem.
    updated[source_index:source_index] = fresh
    assert len(replacements) == 1
    return updated, {"thm_record": source_index + 1, "original_type": theorem["type"],
                     "mutated_type": new_type, "proof_unchanged": True,
                     "replacements": replacements, "added_expression_nodes": len(fresh)}

def check(binary, args, export, timeout=240):
    try:
        p = subprocess.run([binary, *args, str(export)], capture_output=True, timeout=timeout)
        return {"exit_code": p.returncode, "stdout_tail": p.stdout.decode(errors="replace")[-1200:],
                "stderr_tail": p.stderr.decode(errors="replace")[-2400:]}
    except subprocess.TimeoutExpired as e:
        return {"exit_code": 124, "error": "timeout", "seconds": timeout}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--authentic", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--leanchecker", required=True)
    parser.add_argument("--nucleus", required=True)
    args = parser.parse_args()
    output = Path(args.report_dir)
    output.mkdir(parents=True, exist_ok=True)
    genuine = Path(args.authentic)
    report = {"lean_source_commit": LEAN_COMMIT, "format_expected": FORMAT,
              "qualification": "UNKNOWN", "evidence": {}, "verdicts": {}}
    status = 1
    try:
        rows = read(genuine)
        metadata = rows[0]["meta"]
        report["evidence"]["metadata"] = metadata
        assert metadata["format"]["version"] == FORMAT, "NDJSON format/version drift"
        assert metadata["lean"]["githash"] == LEAN_COMMIT, \
            "export Lean hash is not the pinned PR revision"
        _, theorem = find_thm(rows)
        assert theorem["value"] != theorem["type"], "suspicious theorem source IDs"
        report["evidence"]["authentic_sha256"] = sha(genuine.read_bytes())
        report["evidence"]["theorem"] = "ex₁"
        altered, info = mutant(rows)
        forged = output / "mutated-claim.ndjson"
        forged.write_text("".join(json.dumps(x, separators=(",", ":"), ensure_ascii=False)
                                  + "\n" for x in altered))
        report["evidence"]["mutation"] = info
        report["evidence"]["mutant_sha256"] = sha(forged.read_bytes())
        report["evidence"]["authentic_bytes"] = genuine.stat().st_size
        report["evidence"]["mutated_bytes"] = forged.stat().st_size

        for label, file in [("authentic", genuine), ("type-only-2-to-3", forged)]:
            report["verdicts"][label] = {
                "official": check(args.leanchecker, ["--from-export"], file),
                "nucleus": check(args.nucleus, [], file)
            }

        authentic = report["verdicts"]["authentic"]
        corrupted = report["verdicts"]["type-only-2-to-3"]
        assert authentic["official"]["exit_code"] == 0, "official kernel does not ACCEPT authentic"
        assert corrupted["official"]["exit_code"] == 1, "official kernel did not REJECT altered type"
        assert corrupted["nucleus"]["exit_code"] in (1, 2), \
            "Nucleus unsound ACCEPT or execution ERROR on altered proposition"
        if authentic["nucleus"]["exit_code"] == 0:
            report["qualification"] = "WARRANTED_BOUNDED"
            status = 0
        elif authentic["nucleus"]["exit_code"] == 2:
            report["qualification"] = "UNKNOWN_VALID_DECLINED"
        else:
            report["qualification"] = "FAILED_VALID_NOT_ACCEPTED"
    except Exception as exc:
        report["qualification"] = "UNKNOWN_OR_FAILED"
        report["error"] = repr(exc)
    finally:
        (output / "verdict-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    return status

if __name__ == "__main__":
    raise SystemExit(main())
