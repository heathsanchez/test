#!/usr/bin/env python3
"""Source-pinned original/native-mutant Click test and passive obligation audit."""
import hashlib,json,os,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[2]
UP=ROOT/"upstream"
HERE=pathlib.Path(__file__).resolve().parent
SRC=UP/"src/click/types.py"
TEST=UP/"tests/test_types/test_IntRange.py"
PIN="2247b35ea1c47c727d7a06e51fa280e12a863ff6"
TEST_BLOB="7950a23ea3433fd0de98cac41fd81edf358d3f85"
SRC_BLOB="b6e98a965a8fc136f9b1bc16ca7eb3616a21dc1c"
OLD="        raise BadParameter(message, ctx=ctx, param=param)"
BAD="        return None"
OUT=HERE/"result.json"

def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()
def run(label):
    trace=HERE/("trace_"+label+".json")
    trace.unlink(missing_ok=True)
    env=os.environ.copy()
    env["PYTHONPATH"]=str(HERE)+os.pathsep+str(UP/"src")
    env["MG_OBLIGATION_TRACE_JSON"]=str(trace)
    env["MG_ORIGINAL_UPSTREAM_TEST"]=str(TEST)
    st=time.perf_counter()
    p=subprocess.run([sys.executable,"-m","pytest","-q",
             "-p","runtime_obligation_plugin","tests/test_types/test_IntRange.py"],
             cwd=UP,env=env,stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT,text=True,timeout=180)
    try:receipt=json.loads(trace.read_text())
    except (FileNotFoundError,ValueError):receipt={"error":"NO_TRACE_ARTIFACT"}
    return {"label":label,"test_process_seconds":round(time.perf_counter()-st,6),
      "exit_code":p.returncode,"ok":p.returncode==0,
      "tail":p.stdout.strip().splitlines()[-12:],
      "runtime_obligation_receipt":receipt}

def analyze():
    assert git("rev-parse","HEAD")==PIN
    assert git("rev-parse","HEAD:src/click/types.py")==SRC_BLOB
    assert git("rev-parse","HEAD:tests/test_types/test_IntRange.py")==TEST_BLOB
    before=SRC.read_text()
    assert before.count(OLD)==1,"FROZEN_MUTATION_INELIGIBLE"
    after=before.replace(OLD,BAD,1)
    assert after.replace(BAD,OLD,1)==before
    try:
        original=run("original")
        SRC.write_text(after)
        mutant=run("mutant")
    finally:
        SRC.write_text(before)
    b=original["runtime_obligation_receipt"]
    m=mutant["runtime_obligation_receipt"]
    auth=b.get("test_source_sha256")==hashlib.sha256(TEST.read_bytes()).hexdigest()
    same_auth=auth and m.get("test_source_sha256")==b.get("test_source_sha256")
    contexts=b.get("obligations",[])
    mutant_contexts=m.get("obligations",[])
    by_id=lambda r:(r["source_line"],r["expected_exception"])
    original_set={by_id(x) for x in contexts if x.get("native_context_accepted")}
    bad_set={by_id(x) for x in mutant_contexts if x.get("native_context_accepted")}
    invalidated=sorted(original_set-bad_set)
    # It is acceptable that a single test-line has multiple parametrized
    # occurrences; report both source sites and occurrence counts.
    effective=original["ok"] and not mutant["ok"] and same_auth and len(contexts)>0 and (
       b.get("matched_occurrences")==len(contexts)) and bool(invalidated)
    report={"status":"PASS_PROSPECTIVE_RUNTIME_EXCEPTION_AUTHORITY_ACQUISITION"
                 if effective else "UNKNOWN_INCOMPLETE_CAUSAL_RUNTIME_EVIDENCE",
      "upstream":"pallets/click","pinned_upstream_commit":PIN,
      "test_git_blob":TEST_BLOB,"source_git_blob":SRC_BLOB,
      "source_sha256_original":hashlib.sha256(before.encode()).hexdigest(),
      "source_sha256_mutated":hashlib.sha256(after.encode()).hexdigest(),
      "exact_source_mutation":"first raise BadParameter(message, ctx=ctx, param=param) to return None",
      "original":original,"mutant":mutant,
      "source_identity_checked":same_auth,
      "original_obligations_observed":len(contexts),
      "original_obligations_matched":b.get("matched_occurrences"),
      "mutated_obligations_matched":m.get("matched_occurrences"),
      "distinct_contexts_invalidated_by_mutation":[{"line":x[0],"exception":x[1]} for x in invalidated],
      "original_native_suite_green":original["ok"],
      "mutation_caused_native_suite_failure":not mutant["ok"],
      "fair_conventional_baseline":"Upstream pytest same native mutation detection; TIE",
      "relative_advantage":"NOT_DEMONSTRATED",
      "full_release":"UNKNOWN",
      "total_observed_native_seconds":round(original["test_process_seconds"]+mutant["test_process_seconds"],6),
      "limitations":["runtime captured source-authored exception requirements, NOT independent replay",
         "run-time evidence only for pinned tests and execution; no universal implication",
         "author test source identity is pinned, not a cryptographic author signature",
         "no signed cross-language theorem or production-release permission",
         "no economic or defect-detection advantage over original pytest"]}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],
       "observed_original":len(contexts),
       "matched_original":b.get("matched_occurrences"),
       "matched_bad":m.get("matched_occurrences"),
       "invalidated_source_sites":len(invalidated),
       "upstream_original_pass":original["ok"],
       "mutant_upstream_failed":not mutant["ok"],
       "comparison":"TIE"},sort_keys=True))
    if not effective:raise RuntimeError("RUNTIME_EXCEPTION_CAUSAL_QUALIFICATION_UNMET")

if __name__=="__main__":analyze()
