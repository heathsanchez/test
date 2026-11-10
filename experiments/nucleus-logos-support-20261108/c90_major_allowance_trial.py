"""Exact-original paired C89 vs C90 comparison at the standard Arena budget."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess


WORK_KEYS=("outer_spent","outer_remaining","exposure_transitions",
           "replay_reserved_units","recursor_worklist_steps","conversion_pairs")


def parse_work(lines):
    matches=[line for line in lines if line.startswith("NUCLEUS_C47_INNER_WORK:")]
    assert len(matches)==1,"expected one source-qualified failing-root work trace"
    result={}
    for key in WORK_KEYS:
        match=re.search(r"\b"+key+r"=(\d+)",matches[0])
        assert match is not None,key
        result[key]=int(match.group(1))
    return result


def run_trial():
    flags=json.loads(Path("base/flags.json").read_text())
    assert len(flags)==24 and set(flags.values())=={"1"}
    baseline_report=json.loads(Path("reports/c85.json").read_text())
    cases=[
        ("magma-list-pair-n7",8837,"abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21",8827,"b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    results=[]
    for case, expr, expected_hash in cases:
        source=Path(f"arena207/good/perf/{case}.ndjson").read_bytes()
        assert hashlib.sha256(source).hexdigest()==expected_hash
        expected=next(row["observations"][1] for row in baseline_report["rows"] if row["case"]==case)
        env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({"NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
                    "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":str(expr),
                    "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
                    "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1"})
        observations=[]
        for variant,binary in (("C89_baseline","base/nucleus-diagnostic"),
                               ("C90_cap4096","candidate/nucleus-diagnostic")):
            proc=subprocess.run([binary,"262144"],input=source,env=env,capture_output=True,timeout=180)
            assert proc.returncode in (0,2),(case,variant,"unexpected-REJECT-or-crash",proc.returncode)
            stderr=proc.stderr.decode(errors="replace").splitlines()
            work=parse_work(stderr)
            pairs=[line for line in stderr if line.startswith("NUCLEUS_C56_PAIR:")]
            assert pairs,(case,variant,"first-source-pair-missing")
            if variant=="C89_baseline":
                assert proc.returncode==2,(case,"source-baseline-drift")
                assert work==expected["work"],(case,"source-work-baseline-drift")
                assert pairs[0]==expected["first_c56_pair"],(case,"source-pair-baseline-drift")
            observations.append({"variant":variant,"verdict":"ACCEPT" if proc.returncode==0 else "UNKNOWN",
                                 "work":work,"first_pair":pairs[0],
                                 "stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()})
            Path(f"reports/c90-{case}-{variant}.stderr").write_bytes(proc.stderr)
        row={"case":case,"original_sha256":expected_hash,"observations":observations,
             "acceptance_gain":observations[0]["verdict"]=="UNKNOWN" and observations[1]["verdict"]=="ACCEPT",
             "transition_delta":observations[1]["work"]["exposure_transitions"]-observations[0]["work"]["exposure_transitions"]}
        results.append(row)
        print("C90_PAIRED_CASE="+json.dumps({"case":case,"baseline":observations[0]["verdict"],
              "candidate":observations[1]["verdict"],"acceptance_gain":row["acceptance_gain"],
              "transition_delta":row["transition_delta"]},sort_keys=True),flush=True)
    report={"experiment":"C90 source-preserving major exposure cap 512 to 4096",
            "standard_budget":262144,"originals_unchanged":True,"same_shared_owner_fuel":True,
            "no_new_proof_rules":True,"no_403_case_full_regression":True,"rows":results}
    Path("reports/c90.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    run_trial()
