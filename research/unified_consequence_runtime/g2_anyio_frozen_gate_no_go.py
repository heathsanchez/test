#!/usr/bin/env python3
"""Exact bounded G2 selection no-go: read frozen official Actions ZIP inputs.

Usage: python g2_anyio_frozen_gate_no_go.py original_catalog.zip original_admission.zip
This is a source-and-policy audit, never a native candidate trial.
"""
import ast, collections, hashlib, json, pathlib, sys, zipfile

def digest(v):
    return hashlib.sha256(v).hexdigest()

assert len(sys.argv) == 3, "supply pre-existing catalog and admission ZIPs"
archive, admission = [pathlib.Path(p) for p in sys.argv[1:]]
pins = ("3140ce752b3b9b43cba6aafbe914c6e5f48a22f350237965e7ca5ab4edb411ae",
        "2fa8e5c12ec13523a21686dd35e91b72a062ca91db1d1783357af318366a5611")
assert [digest(x.read_bytes()) for x in (archive, admission)] == list(pins)
with zipfile.ZipFile(archive) as z:
    raw = z.read("catalog/COMPLETE_ORIGINAL_CATALOG.json").strip()
    catalog = json.loads(raw)
    index = json.loads(z.read("catalog/SOURCE_ONLY_INDEX.json"))
assert digest(raw) == index["complete_catalog_sha256"] == (
    "7199e478dc9c5dd247571559475bcdbfaa8e737ac21c39bf179cbbe977f4d9c6")
assert len(catalog["rows"]) == 64 and len(catalog["orders"]) == 37
with zipfile.ZipFile(admission) as z:
    original = z.read("training/stage/src/anyio/pytest_plugin.py")
    tests = z.read("training/stage/tests/test_pytest_plugin.py")
    receipts = [json.loads(z.read("training/native-%d.json" % k)) for k in (1,2)]

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

assert git_blob(original) == "d6238cd110ab793ccccb9671fc7eccc33c5415e5"
assert git_blob(tests) == "b15d4da74a17b7f80fa07b0d172c03eb752be7f4"
assert all(r["junit"] == {"passed":40,"failed":2,"errors":0,"skipped":0} for r in receipts)
def nodes(text):
    tree = ast.parse(text)
    return {getattr(n, "name", "top_"+str(i)):ast.dump(n, include_attributes=False)
            for i,n in enumerate(tree.body)}
before = nodes(original.decode())
for row in catalog["rows"]:
    assert row["builder"] == ["SCOPE_NAME"]
    assert row["selector"] == ["Return", "value"]
    assert row["changed_lines"] == [108]
    new = ast.parse(row["candidate"]["replacements"][0]["replacement"])
    after = nodes(row["candidate"]["replacements"][0]["replacement"])
    assert {k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)} == {"_is_auto_mode"}
    func = next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=="_is_auto_mode")
    assert len(func.body)==1 and isinstance(func.body[0],ast.Return)
    assert isinstance(func.body[0].value,ast.Name)

source_tests = ast.parse(tests.decode())
for name in ("test_hypothesis_multiple_backends","test_hypothesis_multiple_backends_in_class"):
    fn = next(n for n in source_tests.body if isinstance(n,ast.FunctionDef) and n.name==name)
    strings = "\n".join(n.value for n in ast.walk(fn) if isinstance(n,ast.Constant) and isinstance(n.value,str))
    assert "@pytest.mark.anyio" in strings and "anyio_backend" in strings

orders = catalog["orders"]
assert "COLD_V104_ORDER" in orders
classes = collections.defaultdict(list)
for name, order in orders.items():
    classes[tuple(order[:8])].append(name)
assert sorted(map(len,classes.values())) == [1,36]
cold = orders["COLD_V104_ORDER"][:8]
other = next(order[:8] for name,order in orders.items() if name!="COLD_V104_ORDER")
assert all(order[:8] == other for name,order in orders.items() if name!="COLD_V104_ORDER")
ids = sorted(set(cold)|set(other))
assert len(ids)==15

def profile(prefix, positive):
    for i,name in enumerate(prefix):
        if name in positive:return (0,2*(i+1))
    return (1,16)
def dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))
totals = collections.Counter()
for bitmask in range(1<<15):
    found={rid for i,rid in enumerate(ids) if bitmask>>i&1}
    c = profile(cold,found)
    n = profile(other,found)
    assert not dominates(n,n)
    verdict = "COLD_UNIQUE_UNAUTHORIZED" if dominates(c,n) else (
        "NONCOLD_36_WAY_TIE" if dominates(n,c) else "ALL_37_TIE")
    totals[verdict]+=1
assert sum(totals.values())==32768
assert totals == {"ALL_37_TIE":10918,"NONCOLD_36_WAY_TIE":10933,"COLD_UNIQUE_UNAUTHORIZED":10917}
# For UNKNOWN native outcomes, identical prefix->identical profile or incomplete.
# Strict Pareto can never elect a uniquely dominating member of 36 equals.
result = {
    "status":"WARRANTED_LOCAL_EXACT_FROZEN_NONCOLD_SELECTION_NO_GO",
    "candidate_count":64,"changed_AST_function":"_is_auto_mode",
    "distinct_prefixes":2,"noncold_equal_policy_names":36,
    "scheduled_unique_candidates":15,"binary_cases":32768,
    "outcome_counts":dict(totals),"native_candidate_executions_here":0,
    "G2":"UNKNOWN__NONCOLD_AUTHORIZATION_IMPOSSIBLE_IN_FROZEN_GATE",
    "future":"SEALED_UNOPENED","limits":"Do not infer candidate-native failure or novel-method inexpressibility."
}
print(json.dumps(result,indent=2,sort_keys=True))
