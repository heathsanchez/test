#!/usr/bin/env python3
"""V11 independently authored source-test obligations -> native witness receipts.

A bounded compiler for literal assert-call == literal patterns; no general natural
language meaning or source-author authentication beyond pinned upstream Git.
"""
import ast,hashlib,importlib, json, os, pathlib, subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];UP=ROOT/"upstream"
HERE=Path(__file__).resolve().parent
SOURCE=UP/"h11/_headers.py"; TEST=UP/"h11/tests/test_headers.py"
PIN="62c5068c971579d61fa1b55373390e12f25fd856"
SOURCE_BLOB="31da3e2b23b55a624b36f105e62a6902e63286aa"
TEST_BLOB="b57274cbbfee8fce3e89f012b6d0f4206f768f67"
OUT=HERE/"result.json"
ORIGINAL_EXPR="        name = name.lower()"
WRONG_EXPR="        name = name.upper()"

def git(*args):
    return subprocess.check_output(["git",*args],cwd=UP,text=True).strip()
def pins():
    assert git("rev-parse","HEAD")==PIN
    assert git("rev-parse","HEAD:h11/_headers.py")==SOURCE_BLOB
    assert git("rev-parse","HEAD:h11/tests/test_headers.py")==TEST_BLOB
    source=SOURCE.read_text();test=TEST.read_text()
    assert source.count(ORIGINAL_EXPR)==1
    return source,test
def literal_safe(x):
    try: return ast.literal_eval(x)
    except (ValueError,TypeError,OverflowError,RecursionError):return None
def acquire_assertions(text):
    tree=ast.parse(text);selected=[];declined=0
    for node in ast.walk(tree):
        if not isinstance(node,ast.Assert):
            continue
        cmp=node.test
        if not isinstance(cmp,ast.Compare) or len(cmp.ops)!=1 or not isinstance(cmp.ops[0],ast.Eq) or len(cmp.comparators)!=1:
            declined+=1;continue
        call=cmp.left
        if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!="normalize_and_validate":
            declined+=1;continue
        if len(call.args)!=1 or call.keywords:
            declined+=1;continue
        value=literal_safe(call.args[0]);expected=literal_safe(cmp.comparators[0])
        if not isinstance(value,(list,tuple)) or not isinstance(expected,(list,tuple)):
            declined+=1;continue
        def pairs(items):
            return all(isinstance(x,(list,tuple)) and len(x)==2 and all(isinstance(y,(bytes,str)) for y in x) for x in items)
        if not pairs(value) or not pairs(expected):
            declined+=1;continue
        selected.append({"line":node.lineno,"input":list(value),
                         "expected":list(expected),
                         "source":ast.get_source_segment(text,node)})
    return selected,declined
def native_obligations(obligations, label):
    # Load the original installed upstream Python module, no source test code is evaluated.
    import h11._headers as headers
    importlib.invalidate_caches()
    outcome=[]
    for item in obligations:
        try:
            actual=list(headers.normalize_and_validate(item["input"]))
            status="MATCH" if actual==item["expected"] else "MISMATCH"
            observed=repr(actual)[:300]
        except Exception as exc:
            status="EXCEPTION";observed=type(exc).__name__
        outcome.append({"line":item["line"],"status":status,
                        "observed":observed})
    return {"label":label,"total":len(outcome),
            "matches":sum(x["status"]=="MATCH" for x in outcome),
            "mismatches":[x for x in outcome if x["status"]!="MATCH"]}
def separate_python(source_version,obligations):
    # Native process obtains freshly loaded source each invocation.
    script=HERE/"witness_worker.py"
    payload=HERE/"cases.json"
    payload.write_text(json.dumps([
       {"input":[[{"encoding":"bytes" if isinstance(v,bytes) else "str","hex":v.hex() if isinstance(v,bytes) else v} for v in pair] for pair in case["input"]],
        "expected":[[{"encoding":"bytes" if isinstance(v,bytes) else "str","hex":v.hex() if isinstance(v,bytes) else v} for v in pair] for pair in case["expected"]],
        "line":case["line"]}
        for case in obligations],indent=2)+"\n")
    env=os.environ.copy();env["PYTHONPATH"]=str(UP)
    t=time.perf_counter()
    proc=subprocess.run([sys.executable,str(script),str(payload)],cwd=UP,env=env,
       text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
    secs=time.perf_counter()-t
    try: receipt=json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:receipt={"status":"ERROR","output":proc.stdout[-500:]}
    return {"source_variant":source_version,"elapsed_seconds":round(secs,6),
            "exit":proc.returncode,"receipt":receipt}
def suite():
    env=os.environ.copy();env["PYTHONPATH"]=str(UP)
    t=time.perf_counter()
    p=subprocess.run([sys.executable,"-m","pytest","-q","h11/tests/test_headers.py"],
        cwd=UP,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
    return {"exit":p.returncode,"ok":p.returncode==0,
            "elapsed_seconds":round(time.perf_counter()-t,6),
            "tail":p.stdout.strip().splitlines()[-7:]}
def documentary_warrant(good):
    # Truthful caller-qualified documentary graph in unchanged MathGraph resolver.
    sys.path.insert(0,str(ROOT/"mathgraph_pinned"))
    from mathgraph_check.warrant_resolution import Claim,Receipt,Route,resolve_graph
    scope="h11:normalize_and_validate:literal-assertions:"+TEST_BLOB
    claims=[Claim(name,"documentary",scope) for name in ("source","witness","property","unrelated","formal_release")]
    receipts=[Receipt(name,"documentary",scope) for name in
              ("source_hash","test_hash","witness_receipt","policy","unrelated_receipt")]
    routes=[Route("source",("source_hash","test_hash")),
            Route("witness",("witness_receipt",)),
            Route("property",("policy",),("source","witness")),
            Route("unrelated",("unrelated_receipt",))]
    initial=frozenset() if good else frozenset({"witness_receipt"})
    full=dict(resolve_graph(claims,routes,receipts,withdrawn=initial).states)
    if good:assert full["property"]=="SOURCE_DOCUMENTED"
    else:assert full["property"]=="UNKNOWN"
    for id_ in ("source_hash","test_hash","witness_receipt","policy"):
        changed=dict(resolve_graph(claims,routes,receipts,
               withdrawn=frozenset(initial|{id_})).states)
        assert changed["property"]=="UNKNOWN" and changed["unrelated"]=="SOURCE_DOCUMENTED"
    assert full["formal_release"]=="UNKNOWN"
    return {"protected":full["property"],"formal_release":full["formal_release"],"withdrawals":4}
def main():
    start=time.perf_counter()
    original,test=pins()
    assertions,declined=acquire_assertions(test)
    assert assertions,"SOURCE_AUTHOR_TEST_NO_ADMISSIBLE_LITERAL_OBLIGATIONS"
    # Author's expected outputs come from AST, not code-written gold labels.
    has_uppercase_input=any(
       any(isinstance(pair[0],str) and pair[0].lower()!=pair[0] for pair in a["input"])
       for a in assertions)
    assert has_uppercase_input,"NO_UPSTREAM_MIXED_CASE_WITNESS"
    test_identity=hashlib.sha256(test.encode()).hexdigest()
    native={}
    try:
        native["original"]=separate_python("original",assertions)
        suite_original=suite()
        # harmless source-comment change, still changes SHA and forces re-admission
        harmless=original+"\n# v11 independently audited no-op comment\n"
        SOURCE.write_text(harmless)
        native["comment_only"]=separate_python("comment_only",assertions)
        suite_harmless=suite()
        # Actual relevant program mutation, not test oracle tampering.
        SOURCE.write_text(original.replace(ORIGINAL_EXPR,WRONG_EXPR,1))
        native["wrong_normalization"]=separate_python("wrong_normalization",assertions)
        suite_wrong=suite()
    finally:
        SOURCE.write_text(original)
    receipts=[native[k]["receipt"] for k in ("original","comment_only","wrong_normalization")]
    native_good=all(x.get("matches",0)==len(assertions) for x in receipts[:2])
    mutation_caught=receipts[2].get("matches",len(assertions))<len(assertions)
    complete=native_good and mutation_caught and suite_original["ok"] and suite_harmless["ok"] and not suite_wrong["ok"]
    statuses={k:documentary_warrant(good=(k!="wrong_normalization" and native_good))
              for k in native}
    # Explicitly flag comment-only changed digest; historical exact source
    # authority must not be silently inherited across changed commits.
    assert hashlib.sha256(harmless.encode()).hexdigest()!=hashlib.sha256(original.encode()).hexdigest()
    report={"status":"WARRANTED_BOUNDED_EXTERNAL_EXECUTABLE_OBLIGATION_ACQUISITION" if complete
              else "REJECTED_OR_UNKNOWN_NATIVE_QUALIFICATION",
       "upstream":"python-hyper/h11","commit":PIN,
       "source_path":"h11/_headers.py","source_sha256":hashlib.sha256(original.encode()).hexdigest(),
       "source_comment_revision_sha256":hashlib.sha256(harmless.encode()).hexdigest(),
       "test_path":"h11/tests/test_headers.py","test_sha256":test_identity,
       "literal_assertions_extracted":len(assertions),"declined_assertions":declined,
       "source_author_obligations": [{"line":x["line"],"source":x["source"]} for x in assertions],
       "mixed_case_input_present":has_uppercase_input,
       "native":native,"native_suite_original":suite_original,
       "native_suite_comment_revision":suite_harmless,"native_suite_wrong_mutation":suite_wrong,
       "source_level_normalization_mutation_detected":mutation_caught,
       "actual_mathgraph_documentary_warrants":statuses,
       "source_change_requalification":"REQUIRED_FOR_NEW_SOURCE_DIGEST",
       "source_grammar":"fixed literal assert equality AST; author wrote expected values",
       "fair_conventional_baseline":"ORIGINAL_UPSTREAM_HEADER_SUITE_DETECTS_SAME_MUTANT",
       "relative_advantage":"NOT_SHOWN",
       "total_elapsed_seconds":round(time.perf_counter()-start,6),
       "full_release":"UNKNOWN",
       "limitations":["earlier inspection exposed some target assertions",
          "source tests are executable examples not a complete natural-language standard",
          "no previously unanticipated semantic grammar inferred",
          "source hashes are caller-qualified, not cryptographic author signatures",
          "comment-only preservation requires new source-version admission",
          "no production GitHub Check or cost superiority"]}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":report["status"],"extracted":len(assertions),
      "declined":declined,"native_matches":[x.get("matches") for x in receipts],
      "mutation_caught":mutation_caught,
      "upstream_tests":[suite_original["ok"],suite_harmless["ok"],suite_wrong["ok"]],
      "relative_advantage":"NOT_SHOWN","full_release":"UNKNOWN"},sort_keys=True))
    if not complete:raise RuntimeError("SOURCE_AUTHOR_WITNESS_NATIVE_QUALIFICATION_FAILED")
if __name__=="__main__":main()
