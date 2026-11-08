"""C78: original NDJSON origin of C77's two different captured functions.

Source reachability is NOT a kernel conversion certificate. Fail closed when
bytes, version, parsed source nodes, or C75 owner identity drift.
"""
import hashlib
import json
import pathlib
import sys

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import c75_fineq_origin as c75

EXPECTED=c75.EXPECTED
TARGETS=(6221,8189)

def inspect(raw):
    owner=c75.inspect(raw)
    assert owner["original_sha256"]==EXPECTED
    names,exprs,decls={}, {}, []
    meta=None
    for line in raw.splitlines():
        r=json.loads(line)
        if "meta" in r:meta=r["meta"]
        if "in" in r:
            ident=int(r["in"])
            if ident in names: raise ValueError("duplicated Name")
            names[ident]=r
        if "ie" in r:
            ident=int(r["ie"])
            if ident in exprs: raise ValueError("duplicated Expr")
            exprs[ident]=r
        for typ in ("axiom","def","thm","opaque"):
            if typ in r:decls.append((typ,r[typ]))
    if meta["format"]["version"]!="3.1.0" or meta["lean"]["githash"]!="5045d0056413266e57c625dcd7c365b10e377c52":
        raise ValueError("exporter semantics changed")
    parent_map={}
    for expr,e in exprs.items():
        for child in c75.children(e):
            if child not in exprs:raise ValueError("undefined Expr child")
            parent_map.setdefault(child,[]).append(expr)
    roots={}
    for root in TARGETS:
        if root not in exprs:raise ValueError("source root missing")
        visited=set()
        stack=[root]
        histogram={}
        while stack:
            expr=stack.pop()
            if expr in visited:continue
            visited.add(expr)
            e=exprs[expr]
            kind=next((k for k in ("app","lam","forallE","letE","const","bvar","natVal","strVal","proj","sort","mdata") if k in e),None)
            if kind is None:raise ValueError("unsupported syntax")
            histogram[kind]=histogram.get(kind,0)+1
            stack.extend(c75.children(e))
        ancestors={root};todo=[root]
        while todo:
            current=todo.pop()
            for ancestor in parent_map.get(current,[]):
                if ancestor not in ancestors:
                    ancestors.add(ancestor)
                    todo.append(ancestor)
        owners=[]
        for kind,d in decls:
            if "value" in d and int(d["value"]) in ancestors:
                owners.append({"kind":kind,"name":c75.name(names,int(d["name"])),
                               "value_expr":int(d["value"])})
        head=root;args=[]
        for _ in range(100):
            e=exprs[head]
            if "app" not in e:break
            args.append(int(e["app"]["arg"]))
            head=int(e["app"]["fn"])
        if "const" in exprs[head]:
            shape=c75.name(names,int(exprs[head]["const"]["name"]))
        elif "bvar" in exprs[head]:
            shape="BVar("+str(exprs[head]["bvar"])+")"
        elif "lam" in exprs[head]:
            shape="Lam"
        else:
            shape="Other("+repr(exprs[head])[:85]+")"
        roots[str(root)]={
            "root_record":exprs[root],
            "source_head":shape,
            "direct_app_args":list(reversed(args)),
            "dag_nodes":len(visited),
            "node_kinds":histogram,
            "literal_source_occurrence_owners":owners[:40],
            "source_occurrence_owner_count":len(owners),
            "unqualified_parent_references":len(parent_map.get(root,[])),
            "context_transport_warrant":"NONE",
        }
    return {"kind":"C78_C77_CAPTURED_FUNCTION_SOURCE_ORIGINS",
        "original_sha256":EXPECTED,
        "C77_captured_roots":[6221,8189],
        "original_lean_git":owner["lean_githash"],
        "owner_matcher":"instDecidableEqFin.match_1",
        "roots":roots,
        "source_ownership_only":True,
        "verified_definitional_conversion":"UNKNOWN",
        "new_standard_accepts":0,
        "checker_changed":False,
        "authorization":"NONE"}

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: c78_source_parent.py original.ndjson result.json")
    raw=pathlib.Path(sys.argv[1]).read_bytes()
    result=inspect(raw)
    pathlib.Path(sys.argv[2]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    for k,v in result["roots"].items():
        print("C78_EXACT_SOURCE="+json.dumps({"root":k,**v},sort_keys=True))
    print("C78_SOURCE_ONLY_NO_ACCEPT",flush=True)
