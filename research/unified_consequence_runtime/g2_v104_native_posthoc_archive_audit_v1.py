#!/usr/bin/env python3
"""Read-only post-outcome audit of already executed AnyIO G2 V104/MSI archive.

No target-specific fix, no new native science and NO opening of protected future.
Python stdlib only. Invocation:
 python g2_v104_native_posthoc_archive_audit_v1.py run-39078910793.zip
"""
import ast,copy,hashlib,json,sys,zipfile
from collections import Counter

DIGEST="7ec7f9922aa3925f8d0d455f79eba414f4512c6210762e7731d442e746972680"
CAT="7199e478dc9c5dd247571559475bcdbfaa8e737ac21c39bf179cbbe977f4d9c6"
H=lambda b:hashlib.sha256(b).hexdigest()
def tree_except(t):
    return [ast.dump(x,include_attributes=False) for x in t.body
            if not (isinstance(x,ast.FunctionDef) and x.name=="_is_auto_mode")]
def shape(t):
    f=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=="_is_auto_mode"]
    assert len(f)==1
    f=copy.deepcopy(f[0])
    returns=[x for x in ast.walk(f) if isinstance(x,ast.Return)]
    assert len(returns)==1 and returns[0] in f.body
    returns[0].value=ast.Constant(value="PLACEHOLDER")
    return ast.dump(f,include_attributes=False)
def main():
    blob=open(sys.argv[1],"rb").read()
    assert H(blob)==DIGEST
    with zipfile.ZipFile(sys.argv[1]) as z:
        assert z.testzip() is None
        get=lambda n:json.loads(z.read(n))
        cat=get("science/SOURCE_ONLY_LOCKED_CATALOG.json")
        assert H(json.dumps(cat,sort_keys=True,separators=(",",":")).encode())==CAT
        assert len(cat["rows"])==64 and len(cat["orders"])==37
        base=ast.parse(z.read("science/native-baseline/stage/src/anyio/pytest_plugin.py"))
        original=z.read("science/native-baseline/stage/src/anyio/pytest_plugin.py")
        for row in cat["rows"]:
            assert row["selector"]==["Return","value"] and row["builder"]==["SCOPE_NAME"]
            assert row["changed_lines"]==[108] and row["features"]=={"K":1000000,"c":1,"v":0.0}
            repl=row["candidate"]["replacements"]
            assert len(repl)==1 and repl[0]["path"]=="src/anyio/pytest_plugin.py"
            assert H(original)==repl[0]["original_sha256"]
            edit=ast.parse(repl[0]["replacement"])
            assert tree_except(edit)==tree_except(base)
            assert shape(edit)==shape(base)
        p=get("science/PRENATIVE_SCHEDULE.json")
        r=get("science/RESULT.json")
        rows=[get("science/CANDIDATE_%03d.json"%i) for i in range(15)]
        assert [x["id"] for x in r["candidate_evaluations"]]==p["candidates"]
        assert len(set(tuple(v[:8]) for v in p["policy_orders"].values()))==2
        counts=Counter(x["status"] for x in rows)
        assert counts=={"VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED":14,"UNKNOWN_NATIVE_EVIDENCE":1}
        junit=Counter()
        for i,x in enumerate(rows):
            assert x["junit_first"]==x["junit_second"]
            if x["status"]=="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED":
                assert x["measured_statuses"]==["FAIL_NATIVE_PROTECTED"]*2
                assert set(x["required"]) <= set(x["executed"])
                j=x["junit_first"];junit[(j["passed"],j["failed"])]+=1
        assert junit=={(40,2):12,(21,9):2}
        unknown=next(i for i,x in enumerate(rows) if x["status"]=="UNKNOWN_NATIVE_EVIDENCE")
        assert "NameError: name 'func' is not defined" in rows[unknown]["native_first"]["stderr_tail"]
        assert rows[unknown]["junit_first"]=={"errors":0,"failed":0,"passed":0,"skipped":0}
        bad_id=p["candidates"][unknown]
        assert sum(bad_id in v[:8] for v in p["policy_orders"].values())==36
        assert r["original_msi_choice"]["complete"]==1
        assert r["selected_training_policy"] is None and r["G2"]=="UNKNOWN"
        assert r["heldout_source"]=="UNOPENED" and r["native_calls_conservatively_charged"]==32
    print(json.dumps({"result":"POSTHOC_AUDIT_PASS_NOT_G2","catalog":64,
                      "trained_candidates":15,"policies":37,"complete_profiles":1,
                      "status_counts":counts,"junit_footprints":{str(k):v for k,v in junit.items()},
                      "future":"UNOPENED","G2":"UNKNOWN"},indent=2))
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python g2_v104_native_posthoc_archive_audit_v1.py <original ZIP>")
    main()
