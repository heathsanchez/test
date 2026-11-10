"""C87 exact source-owned pending Major frame census.

The observation counts *suspended* worklist frames, not completed certified
source values or a warrant to shortcut a major's constructor computation.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess


def parse_c87_pending(lines):
    reports = [json.loads(line.removeprefix("NUCLEUS_C87_PENDING:"))
               for line in lines if line.startswith("NUCLEUS_C87_PENDING:")]
    assert reports, "No C87 root worklist-loss evidence"
    for report in reports:
        for name in ("seq", "parents", "finish_parents", "major_parents",
                     "projected_parents", "major_nonconst", "owner_remaining"):
            assert type(report.get(name)) is int and report[name] >= 0, name
        assert report.get("stage") == "owner-exhausted"
        assert report["owner_remaining"] == 0
        names = report.get("major_const_names")
        assert isinstance(names, dict)
        assert all(isinstance(key, str) and key.isdigit() and
                   type(value) is int and value > 0 for key, value in names.items())
        assert report["finish_parents"] + report["major_parents"] + report["projected_parents"] == report["parents"]
        assert sum(names.values()) + report["major_nonconst"] == report["major_parents"]
    assert len({report["seq"] for report in reports}) == len(reports), "Duplicate C50 tickets"
    return sorted(reports, key=lambda r: r["seq"])


def run_trial():
    flags = json.loads(Path("base/flags.json").read_text())
    assert len(flags) == 24 and set(flags.values()) == {"1"}
    baseline = json.loads(Path("reports/c85.json").read_text())
    assert baseline["observer_off_on_equivalence"] is True
    cases = [
        ("magma-list-pair-n7", 8837, "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21", 8827, "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    work_keys = ("outer_spent", "outer_remaining", "exposure_transitions",
                 "replay_reserved_units", "recursor_worklist_steps", "conversion_pairs")
    rows = []
    for case, profile_expr, expected_hash in cases:
        src = Path("arena207/good/perf/" + case + ".ndjson").read_bytes()
        assert hashlib.sha256(src).hexdigest() == expected_hash
        previous = next(row["observations"][1] for row in baseline["rows"] if row["case"] == case)
        env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({
            "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE": "1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(profile_expr),
            "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE": "1",
            "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR": "1",
            "NUCLEUS_C84_EXACT_CLOSURE_CENSUS": "1",
            "NUCLEUS_C85_COMPLETION_CENSUS": "1",
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS": "1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS": "1",
            "NUCLEUS_C87_PENDING_MAJOR": "1",
        })
        proc = subprocess.run(["candidate/nucleus-diagnostic", "262144"],
                              input=src, env=env, capture_output=True, timeout=180)
        assert proc.returncode == 2, (case, "verdict-changed", proc.returncode)
        log = proc.stderr.decode(errors="replace").splitlines()
        pairs = [ln for ln in log if ln.startswith("NUCLEUS_C56_PAIR:")]
        works = [ln for ln in log if ln.startswith("NUCLEUS_C47_INNER_WORK:")]
        assert pairs and len(works) == 1
        assert pairs[0] == previous["first_c56_pair"]
        work = {key: int(re.search(key + r"=(\d+)", works[0]).group(1))
                for key in work_keys}
        assert work == previous["work"]
        records = parse_c87_pending(log)
        assert any(record["parents"] > 3 for record in records), case
        c87_line = [ln for ln in log if ln.startswith("NUCLEUS_C85_COMPLETED:")]
        assert len(c87_line) == 1
        c85 = json.loads(c87_line[0].split(":", 1)[1])
        assert c85 == {k:v for k,v in previous["c85_completed"].items() if k != "exact_completion_coverage"}
        Path("reports/c87-" + case + ".stderr").write_bytes(proc.stderr)
        rows.append({"case": case, "original_sha256": expected_hash,
                     "observer_changed_original_work": False,
                     "verdict": "UNKNOWN", "events": records,
                     "max_pending": max(records, key=lambda record: record["parents"]),
                     "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()})
        print("C87_ORIGINAL_CASE="+json.dumps({"case":case,"verdict":"UNKNOWN",
             "final_pending": rows[-1]["max_pending"]},sort_keys=True),flush=True)
    result={"experiment":"C87 unfinished Major frame source-name census",
            "standard_budget":262144,"original_proofs_and_C58_source_unchanged":True,
            "new_proof_rule_or_cache":False,"original_standard_accepts":0,
            "full_403_protected_corpus_not_run":True,"rows":rows}
    Path("reports/c87.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    run_trial()
