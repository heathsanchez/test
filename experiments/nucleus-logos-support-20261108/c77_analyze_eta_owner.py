"""Compare the exact BVar1 owner beneath low BVar1 and high η lambda.

Runs after C74_analyze_context on the same original binary and source.
Never establishes equality from expression names, hashes or frame identities.
"""
import json
from pathlib import Path

p=Path("reports/c74.json")
r=json.loads(p.read_text())
assert r["source_sha256"]=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
assert r["proof_rules_changed"] is False
assert r["selected_checker_changed"] is False
assert r["new_original_standard_accepts"] == 0
assert r["results"]["standard"]["verdict"]=="UNKNOWN"
assert r["results"]["diagnostic"]["verdict"]=="ACCEPT"

def event28(arm):
    found=[x for x in r["results"][arm]["contexts"] if x["seq"]==28]
    assert len(found)==1,(arm,"missing C74 event28")
    return found[0]

items={}
for arm,root_expr in [("standard",6),("diagnostic",7369)]:
    row=event28(arm)
    x=row.get("c77_source_parent_slot1")
    assert x is not None,(arm,"source-owned parent observation missing")
    assert x["root_expr"]==root_expr,(arm,x)
    assert x["captures_equivalent_unproved"] is True
    items[arm]=x
    print("C77_OWNER="+json.dumps({"arm":arm,**x},sort_keys=True),flush=True)

a=items["standard"]["outer_slot1"]
b=items["diagnostic"]["outer_slot1"]
if a is None or b is None:
    status="PARENT_CAPTURE_MISSING"
elif a==b:
    status="SAME_DISPLAYED_OWNER_UNPROVED_CONTEXT"
else:
    status="DIFFERENT_DISPLAYED_OWNER_UNPROVED_CONVERSION"
out={
  "experiment":"C77 exact captured semantic owner for source η candidate",
  "source_sha256":r["source_sha256"],
  "selected_checker_changed":False,
  "proof_rules_changed":False,
  "standard_n7_verdict":"UNKNOWN",
  "diagnostic_n7_verdict":"ACCEPT",
  "low":items["standard"],
  "high":items["diagnostic"],
  "observed_parent_relation":status,
  "actual_context_conversion":"NOT_PROVED",
  "capture_and_universe_source_identity":"NOT_PROVED",
  "verified_constructor_certificate":"NOT_BUILT",
  "new_standard_accepts":0,
  "proof_authority":"NONE",
  "next_obligation":"source-typed reconstruction of actual outer-slot1 under each captured frame",
}
Path("reports/c77.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print("C77_PARENT_RELATION="+status)
print("C77_EVIDENCE_ONLY",flush=True)
