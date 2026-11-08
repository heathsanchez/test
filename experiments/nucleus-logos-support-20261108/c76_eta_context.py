"""C76 original source × captured context η-separator, never an equality warrant.

Triangulates C74 actual runtime EnvFrame observations with C75 original NDJSON
owner. Reports the exact η syntactic pattern under a *hypothetical shared*
context, and refuses to infer equality when captured environments differ.
"""
from __future__ import annotations
import importlib.util
import json
import pathlib
import re
import sys

C75 = pathlib.Path(__file__).with_name("c75_fineq_origin.py")
spec=importlib.util.spec_from_file_location("c75_fineq_origin",C75)
c75=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(c75)

EXPECTED_SOURCE=c75.EXPECTED
EXPECTED_C74_SOURCE=EXPECTED_SOURCE

def at_seq(report, arm, seq):
    rows=report["results"][arm]["contexts"]
    hits=[r for r in rows if r["seq"]==seq]
    if len(hits)!=1:raise ValueError("missing/nonunique event")
    return hits[0]

def bind_expr(event, index=0):
    pairs=event["sampled_binders"]
    found=[val for i,val in pairs if i==index]
    if len(found)!=1:raise ValueError("missing/nonunique binder")
    match=re.fullmatch(r"closure:expr=ExprId\((\d+)\):levels=(\d+):captured_env=(\d+)",found[0])
    if not match:raise ValueError("unexpected binder representation")
    return tuple(map(int,match.groups()))

def inspect(original:bytes, c74:dict)->dict:
    owner=c75.inspect(original)
    if c74.get("source_sha256")!=EXPECTED_C74_SOURCE or owner["original_sha256"]!=EXPECTED_SOURCE:
        raise ValueError("original identity drift")
    if c74.get("proof_rules_changed") is not False or c74.get("selected_checker_changed") is not False:
        raise ValueError("C74 observer changed checker")
    if c74.get("new_original_standard_accepts")!=0 or c74.get("same_binary") is not True:
        raise ValueError("C74 comparison boundary drift")
    if c74["results"]["standard"]["verdict"]!="UNKNOWN" or c74["results"]["diagnostic"]["verdict"]!="ACCEPT":
        raise ValueError("source verdicts drift")
    low=at_seq(c74,"standard",28)
    high=at_seq(c74,"diagnostic",28)
    for key in ("recursor","source_expr","source_level_entries"):
        if low[key]!=high[key]:raise ValueError("not matched observer subject: "+key)
    if int(low["source_expr"])!=11 or int(low["recursor"])!=147:
        raise ValueError("actual recursor subject drift")
    a=bind_expr(low)
    b=bind_expr(high)
    if (a[0],b[0])!=(6,7369):
        raise ValueError("not the C75 Fin matcher divergence")
    if a[1]!=b[1]:
        raise ValueError("distinct universe substitutions not transportable")
    if a[2]==b[2] or low["source_env_fingerprint"]==high["source_env_fingerprint"]:
        raise ValueError("expected distinct dynamic contexts; inspect trace")
    # C75 proves unique source ownership of high lambda and actual source syntax,
    # but not that the low BVar1 denotes the same function as high lambda's BVar2.
    if owner["low_event28_binding0"]!={"expr":6,"kind":"BVar","index":1}:
        raise ValueError("low binder source drift")
    if owner["high_event28_binding0"]!={"expr":7369,"kind":"Lam","type":7349,"body":20}:
        raise ValueError("high binder source drift")
    if owner["lambda_body_app"]!={"fn":11,"arg":1}:
        raise ValueError("η body drift")
    # In Lam, BVar2 denotes outer BVar1. BVar0 is the newly bound argument.
    # This establishes a syntactic candidate for η contraction *only*.
    return {
        "experiment":"C76_TYPED_SOURCE_ETA_SHAPE_WITH_DISTINCT_CONTEXTS",
        "original_sha256":EXPECTED_SOURCE,
        "lean_githash":owner["lean_githash"],
        "source_owner":owner["owner_name"],
        "owner_expression":owner["owner_value_expr"],
        "source_lambda_expr":7369,
        "outer_lambda_body":"App(BVar2,BVar0)",
        "syntactically_eta_contracts_to":"BVar1",
        "source_beta_eta_shape":"WARRANTED_SYNTACTIC",
        "runtime_same_recursor":True,
        "runtime_same_universe_entries":True,
        "low_captured_env_id":a[2],
        "high_captured_env_id":b[2],
        "context_content_hashes_differ":True,
        "captured_context_equivalence":"UNKNOWN",
        "definitional_conversion_of_original_closures":"NOT_PROVED",
        "new_standard_accepts":0,
        "selected_checker_changed":False,
        "verification_authority":"NONE",
        "next_obligation":"prove source-typed function equivalence under the actual captured environments",
    }

if __name__=="__main__":
    if len(sys.argv)!=4: raise SystemExit("usage: c76_eta_context.py original.ndjson c74.json c76.json")
    original=pathlib.Path(sys.argv[1]).read_bytes()
    c74=json.loads(pathlib.Path(sys.argv[2]).read_text())
    result=inspect(original,c74)
    pathlib.Path(sys.argv[3]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("C76_ETA_SOURCE_CONTEXT="+json.dumps(result,sort_keys=True))
