#!/usr/bin/env python3
"""Independent offline audit of exact archived Packaging training: NO new inference."""
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
from research.unified_consequence_runtime import g2_pool_first_native_failure_v1 as pool

BASE="332d716676eb934b67ede4054a3e3e0d4022b2d3"
HEAD="a4f5d377a62e96759a4d9237256ec5dc3b19444e"
RAW_SOURCE="a10d2871bb4015855a6e894790949189afff40ae7364fe0210efa91e299fa32e"
TRAINING_ARTIFACT_SHA="62dcffb55a3455d3126fc363faed732aafe1281b2dcb880498214492c8af0b8f"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cmd(args,seconds=125):
    p=subprocess.run(args,capture_output=True,text=True,timeout=seconds)
    assert p.returncode==0,"READ_ONLY_SOURCE_REPLAY:"+p.stderr[-400:]
    return p.stdout.strip()

def main(root,out):
    d=json.loads((root/"RESULT.json").read_text())
    r={"schema":"G2_PACKAGING_REGEX_TRAINING_INDEPENDENT_RECEIPT_AUDIT_V1",
       "status":"UNKNOWN_TRAINING_AUDIT","G2":"UNKNOWN","futures":"SEALED_UNOPENED"}
    assert d["status"]=="CANDIDATE_REGEX_TRAIN_NATIVE_GREEN_AWAITING_AUDIT"
    assert d["G2"]=="UNKNOWN" and d["future"]=="ALL_THREE_SOURCE_UNOPENED"
    original=d["original_training"]
    assert original["repo"]=="pypa/packaging" and original["pr"]==1446
    assert original["status"]=="ADMITTED_FIRST_AUTHENTIC_PROTECTED_NATIVE_FAILURE"
    assert original["source_sha256"]==RAW_SOURCE
    assert original["protected_nodes"]==["tests/test_pylock.py::test_pylock_file_name"]
    assert original["native"]["counts"]=={"tests":5,"failures":1,"errors":0,"skipped":0}
    assert pool.junit(root/"original-admission/native.xml")==original["native"]["counts"]
    assert len(d["candidate_trials"])==1 and d["candidate_count"]==2
    t=d["candidate_trials"][0]
    assert t["kind"]=="strict_terminal_anchor" and t["rank"]==0
    for name,suffix,failures in (
        ("protected","protected",0),("full","full",0),
        ("withdrawal","withdrawal",1),("restoration","restoration",0)):
        log=root/("candidate-00-"+suffix+".log")
        junit=root/("candidate-00-"+suffix+".xml")
        assert log.exists() and junit.exists()
        c=pool.junit(junit)
        m=t[name]
        assert m["counts"]==c and m["junit_sha256"]==sha(junit) and m["log_sha256"]==sha(log)
        assert c["failures"]==failures and c["errors"]==0 and c["skipped"]==0
        assert c["tests"]==(74 if name=="full" else 5)
        assert m["exit"]==(1 if name=="withdrawal" else 0)
        raw=json.loads(log.read_text())
        assert raw["exit"]==m["exit"]
        assert raw["argv"][-1]==("tests/test_pylock.py" if name=="full" else "tests/test_pylock.py::test_pylock_file_name")
        if name!="full":
            x=ET.parse(junit).getroot()
            assert len(list(x.iter("testcase")))==5
            assert all("test_pylock_file_name" in node.attrib["name"] for node in x.iter("testcase"))
    op=json.loads((root/"ACQUIRED_REGEX_OPERATOR.json").read_text())
    assert op["name"]=="strict_terminal_anchor" and op["selected_rank"]==0
    assert op["selected_candidate_sha256"]==t["source_sha256"]
    assert op["original_source_sha256"]==RAW_SOURCE
    assert op["future_source_opened"] is False
    sourcefile=out/"research/unified_consequence_runtime/g2_regex_terminal_genesis_v1.py"
    assert sourcefile.exists() and op["source_file_sha256"]==sha(sourcefile)
    work=Path("/tmp/packaging-independent-offline-audit")
    assert not work.exists()
    cmd(["git","init","-q",str(work)])
    cmd(["git","-C",str(work),"remote","add","origin","https://github.com/pypa/packaging.git"])
    for rev in (BASE,HEAD):
        cmd(["git","-C",str(work),"fetch","-q","--depth=1","--filter=blob:none","--no-tags","origin",rev])
    cmd(["git","-C",str(work),"checkout","-q","--detach",BASE])
    production=work/"src/packaging/pylock.py"
    test=work/"tests/test_pylock.py"
    test.write_bytes(subprocess.check_output(["git","-C",str(work),"show",HEAD+":tests/test_pylock.py"],timeout=35))
    assert sha(production)==RAW_SOURCE and sha(test)==original["head_test_sha256"]
    assert pool.git(work,"diff","--name-only").splitlines()==["tests/test_pylock.py"]
    patch=root/"ACQUIRED_REGEX_OPERATOR.patch"
    x=patch.read_text()
    assert x.startswith("--- original/src/packaging/pylock.py\n+++ generated/src/packaging/pylock.py\n")
    assert x.count("\n--- ")==0 and x.count("\n+++ ")==1
    assert "-_PYLOCK_FILE_NAME_RE" in x and "+_PYLOCK_FILE_NAME_RE" in x
    cmd(["git","-C",str(work),"apply","--check","-p1",str(patch)])
    cmd(["git","-C",str(work),"apply","-p1",str(patch)])
    assert sha(production)==op["selected_candidate_sha256"]
    production.write_bytes(subprocess.check_output(["git","-C",str(work),"show","HEAD:src/packaging/pylock.py"],timeout=35))
    assert sha(production)==RAW_SOURCE
    r.update({"status":"WARRANTED_BOUNDED_PACKAGING_REGEX_TRAINING_NATIVE_RECEIPTS_REPLAYED",
              "original_native":{"tests":5,"failures":1},
              "generated_protected":{"tests":5,"failures":0},
              "full_author_module_tests_passed":74,
              "withdrawal_restored_failure":True,"restoration_reclosed":True,
              "acquired_kind":"strict_terminal_anchor",
              "acquired_patched_source_sha256":t["source_sha256"],
              "operator_source_sha256":op["source_file_sha256"],
              "training_archive_source_run":39113868720,
              "future_native_runs":0,"g2_warrant":False})
    (root/"INDEPENDENT_AUDIT.json").write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print(json.dumps(r,sort_keys=True))

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("auditor ARTIFACT_EVIDENCE_ROOT OUTPUT_ROOT")
    main(Path(sys.argv[1]),Path(sys.argv[2]))
