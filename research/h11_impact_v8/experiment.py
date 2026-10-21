#!/usr/bin/env python3
"""Exact third-party h11 source edit, native trace, mutant and dependency-injection trials.

A trace shows only bounded non-observation in those particular test processes;
it cannot prove full program semantic noninterference.
"""
import hashlib,json,os,pathlib,subprocess,sys,time,statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
SHA="62c5068c971579d61fa1b55373390e12f25fd856"
SOURCE=UP/"h11/_receivebuffer.py"
OWNER=UP/"h11/tests/test_receivebuffer.py"
CANDIDATE=UP/"h11/tests/test_headers.py"
OUT=HERE/"result.json"
OLD="        return bool(len(self))"
NEW="        return len(self) != 0"
BAD="        return False"
TRACER=HERE/"trace_test.py"
SOURCE_GIT_BLOB="e5c4e08a56f5081e87103f38b4add6ce1b730204"
OWNER_BLOB="21a3870b6be9a6a365037326c2085ff2715022cc"
CANDIDATE_BLOB="b57274cbbfee8fce3e89f012b6d0f4206f768f67"

def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()

def run(suite,tag,trace=True):
    import tempfile
    fd,path=tempfile.mkstemp(suffix=".json")
    os.close(fd)
    environ=os.environ.copy()
    environ["PYTHONPATH"]=str(UP)
    start=time.perf_counter()
    p=subprocess.run([sys.executable,str(TRACER),suite,path],cwd=UP,env=environ,
      stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
    elapsed=round(time.perf_counter()-start,6)
    record={}
    try:record=json.loads(pathlib.Path(path).read_text())
    except (OSError,ValueError):record={"trace_status":"MISSING"}
    pathlib.Path(path).unlink(missing_ok=True)
    return {"tag":tag,"suite":suite,"ok":p.returncode==0,"exit":p.returncode,
      "time_seconds":elapsed,"trace":record,"tail":p.stdout.strip().splitlines()[-8:]}

def verify_source_pins():
    assert git("rev-parse","HEAD")==SHA
    assert git("rev-parse","HEAD:h11/_receivebuffer.py")==SOURCE_GIT_BLOB
    assert git("rev-parse","HEAD:h11/tests/test_receivebuffer.py")==OWNER_BLOB
    assert git("rev-parse","HEAD:h11/tests/test_headers.py")==CANDIDATE_BLOB
    source=SOURCE.read_text()
    assert source.count(OLD)==1
    assert "class ReceiveBuffer:" in source and "def __bool__(self)" in source
    return source

def main():
    origin=verify_source_pins()
    tests=[OWNER.relative_to(UP).as_posix(),CANDIDATE.relative_to(UP).as_posix()]
    assert tests==["h11/tests/test_receivebuffer.py","h11/tests/test_headers.py"]
    source_new=origin.replace(OLD,NEW,1)
    source_bad=origin.replace(OLD,BAD,1)
    original_owner=OWNER.read_text()
    original_candidate=CANDIDATE.read_text()
    observed=[]
    try:
        # Baseline, changed, negative mutation all use ORIGINAL unchanged upstream tests.
        for label,source in (("original",origin),("changed",source_new),("bad_mutant",source_bad)):
            SOURCE.write_text(source)
            for suite in tests:
                observed.append(run(suite,label+":"+suite))
        # Inject a separate temporary test into the candidate test file.
        SOURCE.write_text(source_new)
        CANDIDATE.write_text(original_candidate+
            "\n\ndef test_injected_receivebuffer_dependency_v8():\n"
            "    from h11._receivebuffer import ReceiveBuffer\n"
            "    assert bool(ReceiveBuffer()) is False\n")
        injected=run(tests[1],"injected_dependency")
        CANDIDATE.write_text(original_candidate)
        SOURCE.write_text(source_new)
        # Actual paired cost experiment: unchanged source, alternating tests.
        full=[];selected=[]
        for i in range(3):
            order=["full","selected"] if i%2==0 else ["selected","full"]
            for label in order:
                if label=="full":
                    a=run(tests[0],f"cost_{i}:owner")
                    b=run(tests[1],f"cost_{i}:headers")
                    full.append({"seconds":round(a["time_seconds"]+b["time_seconds"],6),
                                 "ok":a["ok"] and b["ok"]})
                else:
                    a=run(tests[0],f"cost_{i}:selected_owner")
                    selected.append({"seconds":a["time_seconds"],"ok":a["ok"]})
    finally:
        SOURCE.write_text(origin)
        CANDIDATE.write_text(original_candidate)
    index={(rec["tag"].split(":")[0],rec["suite"]):rec for rec in observed}
    def case(mode,suite):return index[(mode,suite)]
    source_imports_safe=git("hash-object","h11/tests/test_headers.py")==CANDIDATE_BLOB
    owner_exercises=case("changed",tests[0])["trace"].get("target_calls",0)>0
    candidate_no_calls=case("changed",tests[1])["trace"].get("target_calls",0)==0
    injected_seen=injected["trace"].get("target_calls",0)>0
    mutant_caught=not case("bad_mutant",tests[0])["ok"]
    all_baseline=all(case("original",suite)["ok"] for suite in tests)
    all_changed=all(case("changed",suite)["ok"] for suite in tests)
    measured_scope_ok=all_baseline and all_changed and owner_exercises and candidate_no_calls
    observed_skip_scope=measured_scope_ok and injected_seen and mutant_caught and source_imports_safe
    result={
      "status":"BOUNDED_SESSION_NONOBSERVATION" if observed_skip_scope else "UNKNOWN_NO_CERTIFIED_SESSION_SKIP",
      "upstream":"python-hyper/h11","pin":SHA,
      "target":"h11/_receivebuffer.py:ReceiveBuffer.__bool__",
      "source_change_postexposure":True,
      "original_source_sha256":hashlib.sha256(origin.encode()).hexdigest(),
      "changed_source_sha256":hashlib.sha256(source_new.encode()).hexdigest(),
      "exact_source_only_rewrite":source_new==origin.replace(OLD,NEW,1),
      "original_native_trials":observed,"injected_dependency_trial":injected,
      "negative_mutant_killed":mutant_caught,
      "owner_calls_changed_function":owner_exercises,
      "header_suite_observed_no_calls":candidate_no_calls,
      "header_injection_detected":injected_seen,
      "source_pins_unchanged_after_test":source_imports_safe,
      "actual_candidate_suite_omission":[tests[1]] if observed_skip_scope else [],
      "conventional_equal_info_coverage_selector":"TIE_SAME_SELECTED_SUITE" if observed_skip_scope else "TIE_KEEP_ALL",
      "measured_full":full,"measured_selected":selected,
      "paired_medians_seconds":{
          "full":round(statistics.median(x["seconds"] for x in full),6),
          "selected":round(statistics.median(x["seconds"] for x in selected),6)
      },
      "all_trial_process_seconds":round(sum(x["time_seconds"] for x in observed)
        +injected["time_seconds"]+sum(x["seconds"] for x in full+selected),6),
      "full_release_permission":"UNKNOWN",
      "scope_limits":[
        "absence of calls in one test session does not prove across environments/future tests",
        "module import and tracing side effects not proved impossible",
        "source change designed post exposure; no novel transformation acquired",
        "equal information coverage-based conventional selector can make same skip",
        "all tests actually executed during qualification; no realized total CI savings"
      ]
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],
      "owner_trace_calls":case("changed",tests[0])["trace"].get("target_calls"),
      "header_trace_calls":case("changed",tests[1])["trace"].get("target_calls"),
      "injected_trace_calls":injected["trace"].get("target_calls"),
      "mutant_killed":mutant_caught,
      "native_original":all_baseline,"native_changed":all_changed,
      "candidate_skip":result["actual_candidate_suite_omission"],
      "comparator":result["conventional_equal_info_coverage_selector"],
      "medians":result["paired_medians_seconds"]},sort_keys=True))

if __name__=="__main__":main()
