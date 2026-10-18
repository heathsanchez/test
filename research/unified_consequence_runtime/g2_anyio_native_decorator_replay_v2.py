#!/usr/bin/env python3
"""Independent exact reconciliation of live AnyIO trace with original V104 AST.

Read only original authenticated G2 ZIP and V2 instrumented JSON. No target edits,
new candidate evaluation, G2 qualification, or executing PR #50 access.
"""
import ast
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ORIGINAL_DIGEST = "7ec7f9922aa3925f8d0d455f79eba414f4512c6210762e7731d442e746972680"
ORIGINAL_SOURCE_SHA256 = "a0b5f23acb6f4595b75556ea20e0e166c3ede234b3d941a1e3861e1b69c95f1d"
SRC_IN_ZIP = "science/native-baseline/stage/src/anyio/pytest_plugin.py"
PROTECTED = (
    "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends",
    "tests/test_pytest_plugin.py::test_hypothesis_multiple_backends_in_class",
)
SELECTORS = ("While.test", "If.test", "Return.value", "Call.func", "Call.arg")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def slot_count(fn):
    # Original V14 counts selector-node SOURCE lines inside the function definition.
    # Call decorators lie before fn.lineno and are intentionally excluded.
    nodes = [node for node in ast.walk(fn) if getattr(node, "lineno", 0) >= fn.lineno]
    return (
        sum(isinstance(n, ast.While) for n in nodes)
        + sum(isinstance(n, ast.If) for n in nodes)
        + sum(isinstance(n, ast.Return) for n in nodes)
        + sum(isinstance(n, ast.Call) for n in nodes)
        + sum(len(n.args) for n in nodes if isinstance(n, ast.Call))
    )

def main(original_path, a_path, b_path, output_path):
    raw=Path(original_path).read_bytes()
    assert digest(raw)==ORIGINAL_DIGEST, "ORIGINAL_NATIVE_ARCHIVE_DIGEST"
    with zipfile.ZipFile(original_path) as z:
        assert z.testzip() is None
        src=z.read(SRC_IN_ZIP)
        assert digest(src)==ORIGINAL_SOURCE_SHA256, "ORIGINAL_SOURCE_DIGEST"
    a=json.loads(Path(a_path).read_text())
    b=json.loads(Path(b_path).read_text())
    assert a["production_call_events"]==b["production_call_events"], "RAW_NATIVE_TRACE_REPLAY_CHANGED"
    assert a["junit"]==b["junit"]=={"tests":2,"failures":2,"errors":0,"skipped":0}
    for x in (a,b):
        assert x["status"]=="WARRANTED_BOUNDED_INSTRUMENTED_SOURCE_FUNCTION_OBSERVATION"
        assert x["future_source"]=="UNOPENED" and x["G2"]=="UNKNOWN"
        assert x["v13_original_eligible_guards"]==0
        assert set(x["failure_signatures"])==set(PROTECTED)
        assert all(r["native_one_pass_one_fail"] and not r["blocking_error"]
                   for r in x["failure_signatures"].values())
    tree=ast.parse(src)
    functions=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    # Independently reconstruct the V104 node counts from original source bytes.
    for fn in functions:
        assert slot_count(fn)==a["all_original_v104_source_slot_counts"].get(fn.name,0), "V104_NODE_COUNT_MISMATCH:"+fn.name
    observed={}
    for fn in functions:
        possible_lines={fn.lineno}|{dec.lineno for dec in fn.decorator_list}
        pairs=[]
        for test, entries in a["production_call_events"].items():
            for entry in entries:
                if entry["function"]==fn.name and entry["line"] in possible_lines:
                    pairs.append((test,entry["count"],entry["line"]))
        if pairs:
            assert len(pairs)==len(PROTECTED), "INCOMPLETE_SOURCE_NATIVE_FUNCTION:"+fn.name
            observed[fn.name]={
                "definition_line":fn.lineno,
                "entry_lines":sorted(possible_lines),
                "native_test_count":len(set(t for t,_,_ in pairs)),
                "native_calls":sum(c for _,c,_ in pairs),
                "original_v104_eligible_ast_slots":slot_count(fn),
            }
    raw_calls=a["production_call_events"]
    for test in PROTECTED:
        assert any(e["function"]=="pytest_pyfunc_call" and e["line"]==268 and e["count"]==3
                   for e in raw_calls[test])
        assert any(e["function"]=="run_with_hypothesis" and e["line"]==270 and e["count"]==6
                   for e in raw_calls[test])
    assert observed["pytest_pyfunc_call"]["definition_line"]==269
    assert 268 in observed["pytest_pyfunc_call"]["entry_lines"]
    assert observed["pytest_pyfunc_call"]["original_v104_eligible_ast_slots"]==37
    assert len(observed)==10 and sum(x["original_v104_eligible_ast_slots"] for x in observed.values())==205
    assert set(observed).issuperset({"pytest_pyfunc_call","_is_auto_mode","pytest_pycollect_makeitem"})
    result={
      "schema":"UDM_ANYIO_NATIVE_DECORATOR_NORMALIZATION_V2_INDEPENDENT",
      "status":"WARRANTED_EXACT_SOURCE_NATIVE_OBSERVATION_NO_G2",
      "original_archive_sha256":ORIGINAL_DIGEST,
      "source_sha256":ORIGINAL_SOURCE_SHA256,
      "native_observer":"V2_NONINTRUSIVE_TWO_INDEPENDENT_PROTECTED_PROCESSES",
      "old_summary_eligible_functions":a["eligible_function_count"],
      "old_summary_eligible_slots":a["eligible_source_slot_count"],
      "decorator_normalized_observed_functions":len(observed),
      "decorator_normalized_eligible_slots":sum(x["original_v104_eligible_ast_slots"] for x in observed.values()),
      "critical_function_observed":"pytest_pyfunc_call",
      "critical_function_eligible_v104_slots":37,
      "critical_nested_execution":"run_with_hypothesis 6 calls per protected test",
      "function_evidence":observed,
      "G2":"UNKNOWN","future":"UNOPENED",
      "limitations":"Original author failure preserved, but no direct native closure capture test, no candidate repair or prospective method growth"
    }
    dest=Path(output_path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"observed":len(observed),
        "slots":result["decorator_normalized_eligible_slots"],
        "closure_site":result["critical_function_observed"],"G2":"UNKNOWN"}))

if __name__=="__main__":
    if len(sys.argv)!=5:
        raise SystemExit("usage: audit_original.zip V2_trial_A.json V2_trial_B.json output.json")
    main(*sys.argv[1:])
