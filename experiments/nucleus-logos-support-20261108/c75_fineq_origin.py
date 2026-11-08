"""C75 strict NDJSON provenance for the n7 Fin equality continuation.

No proof rule, reduction rewrite, verified context equality or acceptance is
authorized by graph reachability. Evidence is bound to exact original bytes.
"""
import hashlib
import json
import pathlib
import sys

EXPECTED="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
DIFFERENCE=(7369,7367,7363,7349)

def name(names,n):
    out=[];seen=set()
    while n:
        if n in seen or n not in names:raise ValueError("invalid/cyclic name")
        seen.add(n);r=names[n]
        if "str" in r:
            x=r["str"];out.append(str(x["str"]));n=int(x["pre"])
        elif "num" in r:
            x=r["num"];out.append(str(x["i"]));n=int(x["pre"])
        else:raise ValueError("unknown Name tag")
    return ".".join(reversed(out))

def children(e):
    if "app" in e:return [int(e["app"][k]) for k in ("fn","arg")]
    for k in ("lam","forallE"):
        if k in e:return [int(e[k]["type"]),int(e[k]["body"])]
    if "letE" in e:return [int(e["letE"][k]) for k in ("type","value","body")]
    if "proj" in e:return [int(e["proj"]["struct"])]
    if "mdata" in e:return [int(e["mdata"]["expr"])]
    return []

def inspect(blob):
    sha=hashlib.sha256(blob).hexdigest()
    if sha!=EXPECTED:raise ValueError("original NDJSON SHA changed: "+sha)
    names={};exprs={};decls=[];meta=None
    for line in blob.splitlines():
        r=json.loads(line)
        if "meta" in r:meta=r["meta"]
        if "in" in r:
            i=int(r["in"])
            if i in names:raise ValueError("duplicate Name ID")
            names[i]=r
        if "ie" in r:
            i=int(r["ie"])
            if i in exprs:raise ValueError("duplicate Expr ID")
            exprs[i]=r
        for k in ("def","thm","opaque","axiom"):
            if k in r:decls.append((k,r[k]))
    assert meta["format"]["version"]=="3.1.0"
    assert meta["lean"]["githash"]=="5045d0056413266e57c625dcd7c365b10e377c52"
    assert exprs[6]["bvar"]==1 and exprs[11]["bvar"]==2
    assert exprs[20]["app"]=={"arg":1,"fn":11}
    assert exprs[7369]["lam"]["body"]==20
    assert exprs[7369]["lam"]["type"]==7349
    by_name={name(names,int(d["name"])):(k,d) for k,d in decls}
    owner_kind,owner=by_name["instDecidableEqFin.match_1"]
    assert owner_kind=="def" and int(owner["value"])==7377
    owned=set();stack=[7377]
    while stack:
        i=stack.pop()
        if i in owned:continue
        if i not in exprs:raise ValueError("missing source child")
        owned.add(i)
        stack.extend(children(exprs[i]))
    for i in DIFFERENCE:
        if i not in owned:raise ValueError("binder not in original Fin matcher: "+str(i))
    # Identify ALL declarations whose expression value DAG contains each
    # specialized source term. Assumed-origin controls must be checked,
    # not inferred from expression ID proximity.
    parents={i:[] for i in exprs}
    for parent,e in exprs.items():
        for child in children(e):
            parents.setdefault(child,[]).append(parent)
    findings={}
    for target in DIFFERENCE:
        ancestors={target};todo=[target]
        while todo:
            current=todo.pop()
            for i in parents.get(current,[]):
                if i not in ancestors:
                    ancestors.add(i);todo.append(i)
        owners=[{"kind":k,"name":name(names,int(d["name"])),"value_expr":d.get("value")}
                for k,d in decls if int(d.get("value",-1)) in ancestors]
        if len(owners)!=1 or owners[0]["name"]!="instDecidableEqFin.match_1":
            raise ValueError("non-unique specialized source owner: "+str(target)+repr(owners))
        findings[str(target)]={"record":exprs[target],"value_owners":owners}
    # A source syntax comparison is a causal clue, not a convertibility
    # theorem between differently captured environments.
    return {
       "experiment":"C75 frozen original Fin equality match source attribution",
       "original_sha256":sha,
       "lean_githash":meta["lean"]["githash"],
       "format_version":meta["format"]["version"],
       "owner_name":"instDecidableEqFin.match_1",
       "owner_value_expr":7377,
       "owner_dag_nodes":len(owned),
       "low_event28_binding0":{"expr":6,"kind":"BVar","index":1},
       "high_event28_binding0":{"expr":7369,"kind":"Lam","type":7349,"body":20},
       "lambda_body_app":{"fn":11,"arg":1},
       "source_high_binder_details":findings,
       "inferred_context_equivalence":False,
       "source_reduction_proof_constructed":False,
       "standard_n7_accept":False,
       "kernel_accept_authority":"NONE",
       "selected_checker_changed":False,
    }

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("usage: c75_fineq_origin.py original.ndjson output.json")
    out=inspect(pathlib.Path(sys.argv[1]).read_bytes())
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("C75_SOURCE_ORIGIN="+json.dumps({
        "owner":out["owner_name"],"root":out["owner_value_expr"],
        "owned_nodes":out["owner_dag_nodes"],
        "high_source_ids":sorted(out["source_high_binder_details"]),
        "low_binding":out["low_event28_binding0"],
        "high_binding":out["high_event28_binding0"],
        "authority":out["kernel_accept_authority"]},sort_keys=True))
