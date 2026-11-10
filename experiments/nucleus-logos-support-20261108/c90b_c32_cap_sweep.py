"""C90b: sweep EXISTING C32 diagnostic knob on one exact verified C89 ELF.

No Rust patch, new proof rule, changed source, or fresh build is involved.
The selected native C89 binary has already passed its separate full native
original/forged-proof suite; this sweep additionally replays six frozen
official negative controls at every tested cap.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess


WORK_KEYS=("outer_spent","outer_remaining","exposure_transitions",
           "replay_reserved_units","recursor_worklist_steps","conversion_pairs")


def parse_work(lines):
    records=[line for line in lines if line.startswith("NUCLEUS_C47_INNER_WORK:")]
    assert len(records)==1,"exact first-root profile missing"
    result={}
    for key in WORK_KEYS:
        match=re.search(r"\b"+key+r"=(\d+)",records[0])
        assert match,key
        result[key]=int(match.group(1))
    return result


def parse_c32(lines,expected_cap):
    expression=re.compile(r"^NUCLEUS_C32_MAJOR_GRANT:seq=(\d+):head=NameId\((\d+)\):cap=(\d+):budget=(\d+):owner=Some\((\d+)\)$")
    records=[]
    for line in lines:
        if not line.startswith("NUCLEUS_C32_MAJOR_GRANT:"):
            continue
        match=expression.fullmatch(line)
        assert match,"C32 source cap event format drift"
        seq,head,cap,budget,owner=map(int,match.groups())
        assert cap==expected_cap and budget<=cap and budget<=owner
        records.append({"seq":seq,"head":head,"cap":cap,"budget":budget,"owner":owner})
    assert records and len(records)<=128
    assert len({row["seq"] for row in records})==len(records)
    return records


def run():
    flags=json.loads(Path("base/flags.json").read_text())
    assert len(flags)==24 and set(flags.values())=={"1"}
    verified=json.loads(Path("reports/c85.json").read_text())
    binary="candidate/nucleus-diagnostic"
    cases=[
        ("magma-list-pair-n7",8837,"abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21",8827,"b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    caps=[512,4096,16384]
    rows=[]
    for name,expr,expected_hash in cases:
        src=Path(f"arena207/good/perf/{name}.ndjson").read_bytes()
        assert hashlib.sha256(src).hexdigest()==expected_hash
        c85=next(row["observations"][1] for row in verified["rows"] if row["case"]==name)
        trials=[]
        for cap in caps:
            env={key:value for key,value in os.environ.items() if not key.startswith("NUCLEUS_")}
            env.update(flags)
            env.update({"RUST_MIN_STACK":"16777216",
                        "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
                        "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":str(expr),
                        "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
                        "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
                        "NUCLEUS_DIAGNOSTIC_C32_RECURSOR_MAJOR_GRANT":str(cap)})
            process=subprocess.run([binary,"262144"],input=src,capture_output=True,env=env,timeout=180)
            assert process.returncode in (0,2),(name,cap,"unexpected REJECT or crash",process.returncode)
            lines=process.stderr.decode(errors="replace").splitlines()
            work=parse_work(lines)
            c32=parse_c32(lines,cap)
            pairs=[line for line in lines if line.startswith("NUCLEUS_C56_PAIR:")]
            assert pairs and pairs[0]==c85["first_c56_pair"],(name,cap,"first-root source pair drift")
            if cap==512:
                assert process.returncode==2 and work==c85["work"],(name,"baseline source-work drift")
            trials.append({"cap":cap,"verdict":"ACCEPT" if process.returncode==0 else "UNKNOWN",
                           "work":work,"first_pair":pairs[0],
                           "source_major_samples":len(c32),
                           "major_budgets_ge_512":sum(row["budget"]>=512 for row in c32),
                           "major_owners_ge_4096":sum(row["owner"]>=4096 for row in c32),
                           "max_sample_owner":max(row["owner"] for row in c32),
                           "stderr_sha256":hashlib.sha256(process.stderr).hexdigest()})
            Path(f"reports/c90b-{name}-cap{cap}.stderr").write_bytes(process.stderr)
        rows.append({"case":name,"original_sha256":expected_hash,"trials":trials,
                     "tracked_work_identical":all(t["work"]==trials[0]["work"] for t in trials),
                     "verdicts_identical":len({t["verdict"] for t in trials})==1})
        print("C90B_ORIGINAL_CASE="+json.dumps({"case":name,"caps":caps,
            "verdicts":[t["verdict"] for t in trials],
            "work_identical":rows[-1]["tracked_work_identical"]},sort_keys=True),flush=True)
    bad=["bad/bugs/forged-quot-ind.ndjson","bad/bugs/nat-rec-k-lie.ndjson",
         "bad/bugs/nat-rec-rules.ndjson","bad/bugs/rec-missing-ih.ndjson",
         "bad/bugs/nested-rec-rule-nfields.ndjson","bad/bugs/large-elim-prop-bool.ndjson"]
    negatives=[]
    for source_path in bad:
        src=Path("arena207",source_path).read_bytes()
        records=[]
        for cap in caps:
            env={key:value for key,value in os.environ.items() if not key.startswith("NUCLEUS_")}
            env.update(flags)
            env.update({"RUST_MIN_STACK":"16777216",
                        "NUCLEUS_DIAGNOSTIC_C32_RECURSOR_MAJOR_GRANT":str(cap)})
            p=subprocess.run([binary,"262144"],input=src,capture_output=True,env=env,timeout=180)
            assert p.returncode in (1,2),(source_path,cap,"invalid proof admitted or crashed",p.returncode)
            records.append({"cap":cap,"exit_code":p.returncode})
        negatives.append({"source":source_path,"sha256":hashlib.sha256(src).hexdigest(),"trials":records})
    report={"experiment":"C90b existing exact C32 cap A/B on unchanged C89 ELF",
            "standard_budget":262144,"caps":caps,"no_rust_patch":True,"source_rules_unchanged":True,
            "full_403_protected_corpus_not_run":True,"originals":rows,"negative_controls":negatives}
    Path("reports/c90b.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("C90B_NEGATIVE_CONTROLS_NON_ACCEPT="+str(len(negatives)*len(caps)),flush=True)


if __name__=="__main__":
    run()
