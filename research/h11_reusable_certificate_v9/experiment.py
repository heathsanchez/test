#!/usr/bin/env python3
"""V9 H11 exact-source bounded method-impact reuse audit.

No claim of sound general static noninterference; pinning an observed session
and a strictly syntactic future edit is an explicitly limited guarantee.
"""
import ast, hashlib, json, os, pathlib, statistics, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
OUT=HERE/"result.json"
PIN="62c5068c971579d61fa1b55373390e12f25fd856"
SOURCE=UP/"h11/_receivebuffer.py"
OWNER=UP/"h11/tests/test_receivebuffer.py"
HEADERS=UP/"h11/tests/test_headers.py"
EXPECTED_BLOBS={
 "h11/_receivebuffer.py":"e5c4e08a56f5081e87103f38b4add6ce1b730204",
 "h11/tests/test_receivebuffer.py":"21a3870b6be9a6a365037326c2085ff2715022cc",
 "h11/tests/test_headers.py":"b57274cbbfee8fce3e89f012b6d0f4206f768f67"
}
OLD="        return bool(len(self))"
EDIT={
 "A":"        return len(self) != 0",
 "B":"        return bool(self._data)",
 "C":"        return len(self._data) > 0",
 "D_bad":"        return False"
}
TRACER=HERE/"tracer.py"

def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()
def run_suite(path,tag):
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as f:
        target=f.name
    cmd=[sys.executable,str(TRACER),str(path.relative_to(UP)),target]
    env=os.environ.copy();env["PYTHONPATH"]=str(UP)
    start=time.perf_counter()
    p=subprocess.run(cmd,cwd=UP,text=True,stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,timeout=120,env=env)
    elapsed=time.perf_counter()-start
    try:traced=json.loads(pathlib.Path(target).read_text())
    except (OSError,ValueError):traced={"trace_status":"MISSING"}
    pathlib.Path(target).unlink(missing_ok=True)
    return {"tag":tag,"suite":str(path.relative_to(UP)),
      "ok":p.returncode==0,"exit_code":p.returncode,
      "elapsed_seconds":round(elapsed,6),"trace":traced,
      "tail":p.stdout.strip().splitlines()[-4:]}

def pin():
    assert git("rev-parse","HEAD")==PIN
    for path,sha in EXPECTED_BLOBS.items():
        assert git("rev-parse","HEAD:"+path)==sha,(path,"UPSTREAM_SOURCE_CHANGED")
    original=SOURCE.read_text()
    assert original.count(OLD)==1
    assert "class ReceiveBuffer:" in original and "def __bool__(self)" in original
    return original,HEADERS.read_text()

def structural_admission(original,candidate,test,original_test,approved):
    if hashlib.sha256(test.encode()).digest()!=hashlib.sha256(original_test.encode()).digest():
        return {"admitted":False,"reason":"TEST_SOURCE_IDENTITY_WITHDRAWN"}
    if approved not in EDIT or EDIT[approved]==OLD:
        return {"admitted":False,"reason":"UNKNOWN_TRANSFORMATION"}
    expected=original.replace(OLD,EDIT[approved],1)
    if expected!=candidate:
        return {"admitted":False,"reason":"UNAUTHORIZED_CODE_CHANGE"}
    # AST syntax shape checked but never used to assert arbitrary dynamic semantics.
    oldtree=ast.parse(original)
    newtree=ast.parse(candidate)
    assert ast.dump(oldtree)!=ast.dump(newtree)
    return {"admitted":True,"reason":"EXACT_PINNED_METHOD_BODY_REWRITE",
            "source_digest":hashlib.sha256(candidate.encode()).hexdigest(),
            "suite_digest":hashlib.sha256(test.encode()).hexdigest()}

def main():
    original,header_original=pin()
    # This is a caller-qualified V8 session receipt; not signed external authority.
    original_receipt={"upstream_sha":PIN,"headers_calls_in_original_V8_session":0,
                      "owner_calls_in_original_V8_session":5,
                      "source":"https://github.com/heathsanchez/test/actions/runs/39687187080"}
    assert original_receipt["headers_calls_in_original_V8_session"]==0
    rows=[];sessions=[]
    try:
        for name,new_line in EDIT.items():
            candidate=original.replace(OLD,new_line,1)
            admit=structural_admission(original,candidate,header_original,header_original,name)
            assert admit["admitted"]
            SOURCE.write_text(candidate)
            owner=run_suite(OWNER,name+":owner")
            headers=run_suite(HEADERS,name+":headers")
            # Reuse only a claim about pinned observed header behavior, not a proof that
            # the method return is always correct. The owner test is mandatory.
            accepted=admit["admitted"] and owner["ok"] and headers["ok"] and (
                headers["trace"].get("target_calls")==0)
            rows.append({"variant":name,"certificate":admit,"owner":owner,
              "headers":headers,"source_behavior_retained_in_upstream_tests":owner["ok"],
              "scoped_skip_review":"SOURCE_DOCUMENTED" if accepted else "UNKNOWN",
              "conventional_cached_coverage_decision":"KEEP_OWNER_SKIP_HEADERS" if accepted else "DENY"})
            sessions.extend((owner,headers))
        # Tests authored after V8 exposure. Tampering with pinned independent test
        # invalidates the certificate, even before tracing.
        SOURCE.write_text(original.replace(OLD,EDIT["A"],1))
        tampered=header_original+(
           "\n\ndef test_future_calls_receivebuffer_bool_v9():\n"
           "    from h11._receivebuffer import ReceiveBuffer\n"
           "    assert bool(ReceiveBuffer()) is False\n")
        assert not structural_admission(original,SOURCE.read_text(),tampered,header_original,"A")["admitted"]
        HEADERS.write_text(tampered)
        injected=run_suite(HEADERS,"injected_reference")
        assert injected["trace"].get("target_calls",0)>0
        HEADERS.write_text(header_original)
        # Extending another source expression invalidates the rewrite.
        extra=original.replace(OLD,EDIT["A"],1).replace(
          "        return len(self._data)","        return len(self._data) + 1",1)
        assert not structural_admission(original,extra,header_original,header_original,"A")["admitted"]
        # Change module top-level with a new side-effect; fail closed.
        extra2=original.replace(OLD,EDIT["A"],1)+"\nREUSE_CERTIFICATE_SIDE_EFFECT = True\n"
        assert not structural_admission(original,extra2,header_original,header_original,"A")["admitted"]
    finally:
        SOURCE.write_text(original)
        HEADERS.write_text(header_original)
    assert all(x["headers"]["trace"].get("target_calls")==0 for x in rows)
    assert all(x["owner"]["trace"].get("target_calls",0)>0 for x in rows)
    assert all(x["owner"]["ok"] for x in rows[:3])
    assert not rows[3]["owner"]["ok"],"MALICIOUS_BOOLEAN_EDIT_NOT_CAUGHT"
    assert rows[3]["scoped_skip_review"]=="UNKNOWN"
    assert all(x["scoped_skip_review"]=="SOURCE_DOCUMENTED" for x in rows[:3])
    times={"owner":[x["owner"]["elapsed_seconds"] for x in rows],
           "headers":[x["headers"]["elapsed_seconds"] for x in rows]}
    total=sum(x["elapsed_seconds"] for x in sessions)+injected["elapsed_seconds"]
    result={"status":"WARRANTED_BOUNDED_REUSABLE_SESSION_CERTIFICATE",
      "upstream":"python-hyper/h11","upstream_commit":PIN,
      "original_receipt":original_receipt,
      "accepted_future_variants":3,"rejected_behavior_mutation":1,
      "certified_scope":"exact module outside __bool__ unchanged, exact pinned headers test, specific runner observations",
      "variants":rows,"injected_test":injected,
      "tampered_test_identity_rejected":True,
      "unapproved_method_or_toplevel_edits_rejected":True,
      "conventional_cached_coverage_baseline":"TIE_SAME_DECISIONS",
      "median_per_suite_seconds":{k:round(statistics.median(v),6) for k,v in times.items()},
      "actual_python_process_seconds":round(total,6),
      "hypothetical_elided_header_runs":3,
      "full_release":"UNKNOWN",
      "limitations":["V8 observed trace is historically caller-admitted and not trusted source authentication",
       "same pinned test runner and module import setup assumed for cache validity",
       "no proof that runtime coverage persists under every future input or environment",
       "new local variable refactor can be observed via introspection/tracing",
       "all downstream tests executed for qualification; savings are hypothetical",
       "conventional cached coverage achieves same selection",
       "R7.2 CLC MathGraph unchanged and no formal cross-language adapter"]
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],
       "future":[{"variant":x["variant"],"owner_pass":x["owner"]["ok"],
           "owner_calls":x["owner"]["trace"].get("target_calls"),
           "headers_calls":x["headers"]["trace"].get("target_calls"),
           "skip":x["scoped_skip_review"]} for x in rows],
       "negative_injection_calls":injected["trace"].get("target_calls"),
       "conventional":"TIE","total_process_seconds":result["actual_python_process_seconds"]},sort_keys=True))
if __name__=="__main__":main()
