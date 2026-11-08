"""C72 source-exact major-grant A/B n7 trial. No proof-rule changes.

The candidate's *local* major grant may rise from 512 to 2048.
The caller's shared work owner and all trusted reduction rules remain.
All authentic outcome and malformed-source controls are recorded.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess

ROOT=pathlib.Path("arena207")
REPORT=pathlib.Path("reports")
REPORT.mkdir(exist_ok=True)
PATH="good/perf/magma-list-pair-n7.ndjson"
SOURCE=ROOT.joinpath(PATH).read_bytes()
DIGEST=hashlib.sha256(SOURCE).hexdigest()
assert DIGEST=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
FLAGS=json.loads(pathlib.Path("base/flags.json").read_text())
assert len(FLAGS)==24 and set(FLAGS.values())=={"1"}
VERDICTS={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}
BINARY=str(pathlib.Path("candidate/nucleus-diagnostic").resolve())

def environment(grant):
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(FLAGS)
    env.update({
        "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
        "NUCLEUS_EXPERIMENTAL_RESUMABLE_EXPOSURE":"1",
        "NUCLEUS_C72_SOURCE_MAJOR":"1",
        "NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE":"1",
        "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":"8837",
        "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
        "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
        "NUCLEUS_TRACE_DOWNSTREAM":"1",
    })
    if grant==2048:
        env["NUCLEUS_C72_MAJOR_GRANT_2048"]="1"
    return env

records=[]
for budget in (262144,1048576,4194304,8388608):
    for grant in (512,2048):
        p=subprocess.run([BINARY,str(budget)],input=SOURCE,
             capture_output=True,env=environment(grant),timeout=180)
        verdict=VERDICTS.get(p.returncode,"ERROR")
        lines=p.stderr.decode(errors="replace").splitlines()
        majors=[s for s in lines if s.startswith("NUCLEUS_C72_MAJOR:")]
        assert majors,(budget,grant,"major trace unavailable")
        for event in majors:
            before=int(re.search(r":owner_before=(\d+):",event).group(1))
            after=int(re.search(r":owner_after=(\d+):",event).group(1))
            assert after<=before,(budget,grant,"increased shared owner fuel",event)
        work=[s for s in lines if s.startswith("NUCLEUS_C47_INNER_WORK:")]
        assert len(work)==1,(budget,grant,"root work missing")
        tag=str(budget)+"-grant-"+str(grant)
        (REPORT/("c72-"+tag+".stderr")).write_bytes(p.stderr)
        record={"budget":budget,"local_grant":grant,"verdict":verdict,
                "major_samples":majors,"root_work":work[0],
                "stderr_sha256":hashlib.sha256(p.stderr).hexdigest()}
        print("C72_MAJOR_ARM="+json.dumps({k:v for k,v in record.items() if k!="major_samples"},sort_keys=True),flush=True)
        records.append(record)
        assert verdict in ("ACCEPT","UNKNOWN"),("original valid proof classified invalid/error",record)
    if budget==8388608:
        assert records[-2]["verdict"]=="ACCEPT","resumable 8M baseline drift"

negatives=[]
for name in ("bad/bugs/nat-rec-rules.ndjson","bad/bugs/orphan-rec.ndjson"):
    src=ROOT.joinpath(name).read_bytes()
    p=subprocess.run([BINARY,"262144"],input=src,capture_output=True,
                     env=environment(2048),timeout=120)
    verdict=VERDICTS.get(p.returncode,"ERROR")
    assert verdict in ("REJECT","UNKNOWN"),("unsound invalid input ACCEPT",name,verdict)
    result={"path":name,"source_sha256":hashlib.sha256(src).hexdigest(),"verdict":verdict}
    print("C72_NEGATIVE="+json.dumps(result,sort_keys=True),flush=True)
    negatives.append(result)
report={"experiment":"C72 source-bound local recursor-major grant 512 vs 2048",
        "source_sha256":DIGEST,"standard_budget":262144,
        "source_unchanged":True,"proof_rules_changed":False,
        "selected_checker_changed":False,"full_protected_403_not_run":True,
        "records":records,"negative_controls":negatives}
(REPORT/"c72.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
