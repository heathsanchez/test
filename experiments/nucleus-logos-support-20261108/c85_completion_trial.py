"""C85 completion observer: verify unchanged original source work and verdicts.

The completed work units include nested child evaluations, so they are *not*
independent cost savings. Nothing inferred here authorizes cache reuse.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def parse_c85_summary(lines):
    matching = [line.removeprefix("NUCLEUS_C85_COMPLETED:")
                for line in lines if line.startswith("NUCLEUS_C85_COMPLETED:")]
    assert len(matching) == 1, "C85 selected root must emit exactly one report"
    data = json.loads(matching[0])
    needed = ("completed", "unique_exact", "repeated_exact", "repeated_inclusive_work",
              "completed_inclusive_work", "one_step_exits", "cache_hits", "unkeyed_completions", "overflow",
              "limit", "goal_counts")
    assert all(name in data for name in needed), "C85 report incomplete"
    assert data["source_authority_preserved"] is True
    assert data["exact_structural_comparison"] is True
    assert data["completed_only"] is True
    assert data["inclusive_cost_not_realizable_savings"] is True
    for name in needed[:-1]:
        assert type(data[name]) is int and data[name] >= 0, (name, data[name])
    assert data["limit"] == 8192
    assert data["overflow"] == 0, "C85 observer capacity overflow: cannot claim exhaustive census"
    assert set(data["goal_counts"]) == {"Completed", "OneStep"}
    assert sum(data["goal_counts"].values()) == data["completed"]
    assert data["unique_exact"] + data["repeated_exact"] == data["completed"]
    assert data["repeated_inclusive_work"] <= data["completed_inclusive_work"]
    data["exact_completion_coverage"] = data["unkeyed_completions"] == 0
    return data


def run_trial():
    flags = json.loads(Path("base/flags.json").read_text())
    assert len(flags) == 24 and set(flags.values()) == {"1"}
    cases = [
        ("magma-list-pair-n7", 8837,
         "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21", 8827,
         "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    work_keys = ["outer_spent", "outer_remaining", "exposure_transitions",
                 "replay_reserved_units", "recursor_worklist_steps", "conversion_pairs"]
    Path("reports").mkdir(exist_ok=True)
    rows = []
    for case, profile_expr, expected_hash in cases:
        src = Path("arena207/good/perf/" + case + ".ndjson").read_bytes()
        assert hashlib.sha256(src).hexdigest() == expected_hash
        observations = []
        for enabled in (False, True):
            env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
            env.update(flags)
            env.update({
                "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE": "1",
                "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(profile_expr),
                "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE": "1",
                "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR": "1",
                "NUCLEUS_C84_EXACT_CLOSURE_CENSUS": "1",
            })
            if enabled:
                env["NUCLEUS_C85_COMPLETION_CENSUS"] = "1"
            proc = subprocess.run(["candidate/nucleus-diagnostic", "262144"],
                                  input=src, capture_output=True, env=env, timeout=180)
            verdict = {0: "ACCEPT", 1: "REJECT", 2: "UNKNOWN", 3: "ERROR"}.get(proc.returncode, "ERROR")
            assert verdict == "UNKNOWN", (case, enabled, verdict)
            log = proc.stderr.decode(errors="replace").splitlines()
            works = [line for line in log if line.startswith("NUCLEUS_C47_INNER_WORK:")]
            pairs = [line for line in log if line.startswith("NUCLEUS_C56_PAIR:")]
            assert len(works) == 1 and pairs, (case, enabled, len(works), len(pairs))
            work = {key: int(re.search(key + r"=(\d+)", works[0]).group(1))
                    for key in work_keys}
            c84 = [line for line in log if line.startswith("NUCLEUS_C84_CLOSURES:")]
            assert len(c84) == 1
            completed = parse_c85_summary(log) if enabled else None
            if not enabled:
                assert not any(line.startswith("NUCLEUS_C85_COMPLETED:") for line in log)
            fname = f"reports/c85-{case}-{'observer' if enabled else 'baseline'}.stderr"
            Path(fname).write_bytes(proc.stderr)
            observations.append({
                "observer": enabled,
                "verdict": verdict,
                "first_c56_pair": pairs[0],
                "work": work,
                "c84_closure_census": json.loads(c84[0].split(":", 1)[1]),
                "c85_completed": completed,
                "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(),
            })
        assert observations[0]["first_c56_pair"] == observations[1]["first_c56_pair"]
        assert observations[0]["work"] == observations[1]["work"]
        assert observations[0]["c84_closure_census"] == observations[1]["c84_closure_census"]
        rows.append({"case": case, "original_sha256": expected_hash,
                     "observer_off_on_equivalent": True, "observations": observations})
        print("C85_ORIGINAL_CASE=" + json.dumps({
            "case": case, "standard_budget": 262144,
            "both_unknown": True,
            "completed": observations[1]["c85_completed"],
        }, sort_keys=True), flush=True)
    result = {
        "experiment": "C85 source-qualified completed recursor inclusive-cost census",
        "original_proofs_and_C58_source_unchanged": True,
        "standard_budget": 262144,
        "new_proof_rule_or_cache": False,
        "observer_off_on_equivalence": True,
        "original_standard_accepts": 0,
        "full_403_protected_corpus_not_run": True,
        "rows": rows,
    }
    Path("reports/c85.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    run_trial()
