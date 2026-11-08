"""Source-qualified exact countermodel operation; no kernel reduction shortcut."""
import importlib.util
import json
import pathlib
import sys

MOD=pathlib.Path(__file__).with_name("c65_source_inventory.py")
spec=importlib.util.spec_from_file_location("c65_source_inventory",MOD)
c65=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c65)

def report(src):
    names,exprs,decls=c65.parse(src)
    out={"kind":"C67_ORIGINAL_OPERATION_SOURCE_NOT_PROOF",
         "source_sha256":c65.EXPECTED_SOURCE,
         "nucleus_accept_authority":"NONE","verified_reduction":"UNKNOWN"}
    owners={}
    for kind,d in decls:
        if "name" not in d:continue
        n=c65.resolve_name(int(d["name"]),names)
        if n in ("countermodel.op","countermodel.inst","EquationLHS","Magma.op"):
            entry={"name":n,"kind":kind,"type":int(d["type"]),
                   "value":int(d["value"]) if "value" in d else None}
            if entry["value"] is not None:
                entry["value_source"]=c65.summarize(entry["value"],names,exprs)
                owned=reach(exprs,entry["value"])
                entry["literal_nat_values"]=sorted({
                    str(exprs[i]["natVal"]) for i in owned if "natVal" in exprs[i]
                })
            owners[n]=entry
    for n in ("countermodel.op","countermodel.inst","EquationLHS"):
        if n not in owners:raise ValueError("required source definition missing: "+n)
    out["definitions"]=owners
    return out

def reach(exprs, root):
    seen=set();stack=[root]
    while stack:
        i=stack.pop()
        if i in seen:continue
        seen.add(i)
        stack.extend(c65.dependencies(exprs,i))
    return seen

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: c67_operation_source.py input.ndjson output.json")
    out=report(pathlib.Path(sys.argv[1]).read_bytes())
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    for name,v in out["definitions"].items():
        summary=v.get("value_source",{})
        print("C67_REAL_SOURCE="+json.dumps({"name":name,"kind":v["kind"],"value":v["value"],
          "head":summary.get("head"),"consts":summary.get("named_consts"),
          "source_dag_nodes":summary.get("dag_nodes"),
          "source_hash":summary.get("subdag_sha256"),
          "nat_values":v.get("literal_nat_values")},sort_keys=True))
    print("C67_ACCEPT_AUTHORITY=NONE")
