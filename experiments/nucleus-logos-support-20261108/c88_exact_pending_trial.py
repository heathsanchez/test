"""C88 compare unfinished Major *neutral identities* at C50 exhaustion.

Full Neutral equality includes recursor name, universe levels, complete
pending argument closure spine and conservative captured immutable EnvFrame
node identity. A repeated name alone never licenses sharing.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess


def parse_c88(lines):
    reports = [json.loads(line.removeprefix("NUCLEUS_C88_EXACT_PENDING:"))
               for line in lines if line.startswith("NUCLEUS_C88_EXACT_PENDING:")]
    assert reports, "C88 report missing"
    for item in reports:
        for name in ("seq", "major_parents", "unique_exact_neutrals", "exact_repeats"):
            assert type(item.get(name)) is int and item[name] >= 0, name
        assert item["full_captured_spine_and_environment"] is True
        assert item["same_source_name_alone_insufficient"] is True
        assert item["unique_exact_neutrals"] + item["exact_repeats"] == item["major_parents"]
    assert len({record["seq"] for record in reports}) == len(reports)
    return sorted(reports, key=lambda x: x["seq"])


def run_trial():
    flags = json.loads(Path("base/flags.json").read_text())
    assert len(flags) == 24 and set(flags.values()) == {"1"}
    previous = json.loads(Path("reports/c87.json").read_text())
    c85_baseline = json.loads(Path("reports/c85.json").read_text())
    cases = [
        ("magma-list-pair-n7", 8837, "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21", 8827, "b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    work_keys = ("outer_spent", "outer_remaining", "exposure_transitions",
                 "replay_reserved_units", "recursor_worklist_steps", "conversion_pairs")
    rows=[]
    for case, profile_expr, expected_hash in cases:
        src=Path("arena207/good/perf/"+case+".ndjson").read_bytes()
        assert hashlib.sha256(src).hexdigest() == expected_hash
        expected=next(row for row in previous["rows"] if row["case"]==case)
        expected_c85=next(row["observations"][1] for row in c85_baseline["rows"] if row["case"]==case)
        env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({
            "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":str(profile_expr),
            "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
            "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
            "NUCLEUS_C84_EXACT_CLOSURE_CENSUS":"1",
            "NUCLEUS_C85_COMPLETION_CENSUS":"1",
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS":"1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS":"1",
            "NUCLEUS_C87_PENDING_MAJOR":"1",
            "NUCLEUS_C88_EXACT_PENDING":"1",
        })
        proc=subprocess.run(["candidate/nucleus-diagnostic","262144"],
                            input=src,capture_output=True,env=env,timeout=180)
        assert proc.returncode==2,(case,"verdict-changed",proc.returncode)
        log=proc.stderr.decode(errors="replace").splitlines()
        works=[ln for ln in log if ln.startswith("NUCLEUS_C47_INNER_WORK:")]
        assert len(works)==1
        work={key:int(re.search(key+r"=(\d+)",works[0]).group(1)) for key in work_keys}
        assert work==expected_c85["work"]
        pairs=[ln for ln in log if ln.startswith("NUCLEUS_C56_PAIR:")]
        assert pairs and pairs[0]==expected_c85["first_c56_pair"]
        c85_lines=[ln for ln in log if ln.startswith("NUCLEUS_C85_COMPLETED:")]
        assert len(c85_lines)==1
        assert json.loads(c85_lines[0].split(":",1)[1])=={
            k:v for k,v in expected_c85["c85_completed"].items() if k!="exact_completion_coverage"}
        c87=[json.loads(ln.removeprefix("NUCLEUS_C87_PENDING:")) for ln in log
             if ln.startswith("NUCLEUS_C87_PENDING:")]
        assert c87==expected["events"]
        records=parse_c88(log)
        assert [x["seq"] for x in records]==[x["seq"] for x in c87]
        for prior,new in zip(c87,records):
            assert prior["major_parents"]==new["major_parents"]
        Path("reports/c88-"+case+".stderr").write_bytes(proc.stderr)
        rows.append({"case":case,"original_sha256":expected_hash,
                     "verdict":"UNKNOWN","standard_work_unchanged":True,
                     "records":records,"max_pending":max(records,key=lambda x:x["major_parents"]),
                     "stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()})
        print("C88_ORIGINAL_CASE="+json.dumps({"case":case,"verdict":"UNKNOWN",
            "max_pending":rows[-1]["max_pending"]},sort_keys=True),flush=True)
    result={"experiment":"C88 exact pending Major source-neutral identity census",
            "standard_budget":262144,"selected_C58_source_unchanged":True,
            "no_accept_or_proof_rule_changed":True,"original_standard_accepts":0,
            "full_403_protected_corpus_not_run":True,"rows":rows}
    Path("reports/c88.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")


if __name__ == "__main__":
    run_trial()
