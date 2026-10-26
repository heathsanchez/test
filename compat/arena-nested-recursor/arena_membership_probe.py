#!/usr/bin/env python3
"""Pinned Nucleus/Arena NDJSON differential: authentic nfields exploit and membership mutants."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BAD_SHA = "8874ecde1a57edbc52428cb7ea7c8834f74e623a164b0c0f69e78613effc0c56"
BASELINE = Path("metatron-kernel/evidence/performance/owned-environment-2026-10-13/nucleus-owned-environment-frozen196.json")
BIN = Path("metatron-kernel/target/release/metatron-kernel")
OUT = Path("/tmp/nucleus-arena-membership-evidence")
GOOD_ROOT = Path("/tmp/nucleus-frozen-inputs")
BAD_ROOT = Path("/tmp/nucleus-arena-inputs")

def digest(b):
    return hashlib.sha256(b).hexdigest()

def verdict(p):
    with p.open("rb") as stdin:
        r = subprocess.run([str(BIN)], stdin=stdin, capture_output=True, timeout=160)
    return {"path": str(p), "sha256": digest(p.read_bytes()), "exit_code": r.returncode,
            "diagnostic_tail": (r.stdout + r.stderr).decode(errors="replace")[-1500:]}

def mutate(lines, index, value, label):
    output = OUT / (label + ".ndjson")
    updated = lines.copy()
    updated[index] = (json.dumps(value, separators=(",", ":")) + "\n").encode()
    output.write_bytes(b"".join(updated))
    return output

def run():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        found = [(p, digest(p.read_bytes())) for p in BAD_ROOT.rglob("*nested-rec-rule-nfields*.ndjson")]
        exact = [p for p, sha in found if sha == BAD_SHA]
        assert len(exact) == 1, f"source-hash mismatch or missing official exploit: {found}"
        bad = exact[0]
        assert json.loads(bad.read_text().splitlines()[0])["meta"]["format"]["version"] == "3.1.0"
        r = verdict(bad); results.append({"case": "official-Arena-bad-False", **r})
        assert r["exit_code"] == 1, r

        rows = json.loads(BASELINE.read_text())["modes"]["default"]["rows"]
        candidates = []
        for row in rows:
            if row["rc"] != 0 or row["group"] != "good":
                continue
            path = GOOD_ROOT / row["case"]
            if not path.is_file() or path.stat().st_size > 4_000_000:
                continue
            source = path.read_bytes()
            assert digest(source) == row["sha256"], f"frozen-input byte mismatch: {path}"
            lines = source.splitlines(keepends=True)
            for i, line in enumerate(lines):
                if b'"inductive"' not in line:
                    continue
                obj = json.loads(line)
                block = obj.get("inductive")
                if block and block.get("types") and block["types"][0].get("ctors") and block["types"][0].get("all"):
                    candidates.append((path, row, lines, i, obj))
                    break
        assert candidates, "no SHA-pinned previously ACCEPTED inductive positive available"
        candidates.sort(key=lambda c: (
            not any(t.get("numNested", 0) > 0 for t in c[4]["inductive"]["types"]),
            c[0].stat().st_size, str(c[0])))
        positive, pinned, lines, line_number, original = candidates[0]
        r = verdict(positive)
        results.append({"case": "original-accepted-inductive", "pinned_case": pinned["case"], **r})
        assert r["exit_code"] == 0, r

        a = copy.deepcopy(original)
        ctors = a["inductive"]["types"][0]["ctors"]
        if len(ctors) > 1: ctors[1] = ctors[0]
        else: ctors.append(ctors[0])
        assert a != original
        pa = mutate(lines, line_number, a, "duplicated-ctors")
        r = verdict(pa)
        results.append({"case": "duplicate-inductive-constructor-membership", "changed_line": line_number + 1,
                        "changed_path": "inductive.types[0].ctors", **r})
        assert r["exit_code"] in (1, 2), f"unsound ACCEPT or execution ERROR: {r}"

        b = copy.deepcopy(original)
        members = b["inductive"]["types"][0]["all"]
        if len(members) > 1: members.pop()
        else: members.append(members[0])
        assert b != original
        pb = mutate(lines, line_number, b, "incorrect-all")
        r = verdict(pb)
        results.append({"case": "inductive-family-membership", "changed_line": line_number + 1,
                        "changed_path": "inductive.types[0].all", **r})
        assert r["exit_code"] in (1, 2), f"unsound ACCEPT or execution ERROR: {r}"
        # Mutation C: keep the constructor name and type intact, but assign its
        # declared ownership to a *different existing* inductive type. This
        # isolates block ownership rather than replacing a name with a missing ID.
        available_names = set()
        for line in lines:
            if b'"inductive"' in line:
                candidate_block = json.loads(line).get("inductive")
                if candidate_block:
                    available_names.update(t["name"] for t in candidate_block["types"])
        current_owner = original["inductive"]["ctors"][0]["induct"]
        foreign = sorted(available_names - {current_owner})
        if foreign:
            c = copy.deepcopy(original)
            c["inductive"]["ctors"][0]["induct"] = foreign[0]
            pc = mutate(lines, line_number, c, "incorrect-ctor-owner")
            r = verdict(pc)
            results.append({"case": "constructor-owner-relocation",
                            "changed_line": line_number + 1,
                            "changed_path": "inductive.ctors[0].induct",
                            "original_owner": current_owner, "foreign_owner": foreign[0], **r})
            assert r["exit_code"] in (1, 2), f"unsound ACCEPT or execution ERROR: {r}"
        else:
            results.append({"case": "constructor-owner-relocation", "status": "UNKNOWN_NO_FOREIGN_TYPE"})
        report = {"status": "PASS_BOUNDED_MUTATIONS", "official_export_sha256": BAD_SHA,
                  "pinned_positive_sha256": pinned["sha256"], "results": results}
        rc = 0
    except Exception as error:
        report = {"status": "UNKNOWN_OR_FAILURE", "error": repr(error), "results": results}
        rc = 1
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return rc

if __name__ == "__main__":
    sys.exit(run())
