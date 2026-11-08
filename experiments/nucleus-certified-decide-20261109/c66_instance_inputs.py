"""Trace source-exact n7 Nat.decidableForallFin arguments and imported definitions.

Extends C65 without changing its frozen source or granting verification authority.
"""
from __future__ import annotations
import importlib.util
import json
import pathlib
import sys

MODULE=pathlib.Path(__file__).with_name("c65_source_inventory.py")
spec=importlib.util.spec_from_file_location("c65_source_inventory", MODULE)
c65=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(c65)

ROOTS=(6083,8749,8773,8795,8796,8799)
NAMES=("Nat.decidableForallFin","Nat.decidableBallLT","Nat.decidableBallLTTR",
       "decidable_of_iff","Decidable.decide","instDecidableEqFin")
def report(source:bytes) -> dict:
    names,exprs,declarations=c65.parse(source)
    meta=json.loads(source.splitlines()[0])["meta"]
    targets=[]
    for kind,d in declarations:
        if "name" not in d: continue
        name=c65.resolve_name(int(d["name"]),names)
        if any(name==needle or name.endswith("."+needle) for needle in NAMES):
            targets.append({"name":name,"kind":kind,"type":int(d["type"]),
              "value":int(d.get("value",-1)),"levelParams":d.get("levelParams",[])})
    details={str(i):c65.summarize(i,names,exprs) for i in ROOTS}
    predicate_name="Nat.decidableForallFin"
    assert details["8796"]["head"]==predicate_name,details["8796"]["head"]
    assert details["8799"]["head"]=="Decidable.decide"
    assert details["8796"]["direct_spine_arguments"]==[6083,8773,8795]
    assert details["8799"]["direct_spine_arguments"]==[8749,8796]
    return {"kind":"C66_EXACT_SOURCE_INPUTS_NOT_CERTIFICATE",
       "source_sha256":c65.EXPECTED_SOURCE,
       "exporter_meta":meta,
       "source_root_exprs":details,
       "matched_declarations":targets,
       "verification_authority":"NONE",
       "kernel_replay":"NOT_RUN",
       "requires_original_definitional_equality":True,
    }

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: c66_instance_inputs.py input.ndjson output.json")
    raw=pathlib.Path(sys.argv[1]).read_bytes()
    obj=report(raw)
    pathlib.Path(sys.argv[2]).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print("C66_EXPORTER_META="+json.dumps(obj["exporter_meta"],sort_keys=True))
    print("C66_MATCHED_DEFS="+json.dumps(obj["matched_declarations"],sort_keys=True))
    for name,node in obj["source_root_exprs"].items():
        print("C66_SOURCE_INPUT="+json.dumps({
            "expr":name,"head":node["head"],"dag_nodes":node["dag_nodes"],
            "spine":node["direct_spine_arguments"],
            "kinds":node["expr_kinds"],
            "named_consts":node["named_consts"]
        },sort_keys=True))
    print("C66_ACCEPT_AUTHORITY=NONE")
