#!/usr/bin/env python3
"""Predeclared, human-designed, source-bound sequence repair candidate grammar."""
import ast,hashlib,json,os,pathlib,subprocess,sys,tempfile,time,difflib,re
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import sequence_observer as seq
prior=seq.native

def methods(cls):
    return {x.name:x for x in cls.body if isinstance(x,ast.FunctionDef)}
def start(m):
    a=m.body
    if isinstance(a[0],ast.Expr) and isinstance(a[0].value,ast.Constant) and isinstance(a[0].value.value,str):
        return a[1].lineno
    return a[0].lineno
def insert_lines(src,updates):
    ls=src.splitlines(keepends=True)
    for at,text in sorted(updates,key=lambda a:a[0],reverse=True):ls.insert(at-1,text)
    patched="".join(ls)
    compile(patched,"<source-generated-repair>","exec")
    return patched
def mk(src,cand):
    tree=ast.parse(src)
    cl=[x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==cand["class"]]
    if len(cl)!=1:raise ValueError("UNKNOWN_OWNER")
    owner=cl[0]; ms=methods(owner);entry=cand["public_entrypoints"]
    if "insert" in entry or "__setitem__" in entry:
        app=ms.get("append")
        if not app:raise ValueError("UNKNOWN_NO_SOURCE_SIBLING_NORMALIZER")
        inp=app.args.args[-1].arg
        convert=set();guards=set()
        for n in ast.walk(app):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="append" and len(n.args)==1:
                q=n.args[0]
                if isinstance(q,ast.Call) and isinstance(q.func,ast.Name) and len(q.args)==1 and isinstance(q.args[0],ast.Name) and q.args[0].id==inp:convert.add(q.func.id)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="isinstance" and len(n.args)==2 and isinstance(n.args[0],ast.Name) and n.args[0].id==inp:
                z=ast.get_source_segment(src,n.args[1])
                if z:guards.add(z)
        if len(convert)!=1 or len(guards)!=1:raise ValueError("UNKNOWN_UNPROVEN_NORMALIZATION")
        typ=convert.pop();guard=guards.pop();changes=[]
        if "insert" in entry:
            if "insert" in ms:raise ValueError("UNKNOWN_EXISTING_INSERT_NEEDS_REWRITE")
            pad=" "*(owner.col_offset+4)
            code=("\n"+pad+"def insert(self, index, value):\n"
                  +pad+"    if isinstance(value, "+guard+") and not isinstance(value, "+typ+"):\n"
                  +pad+"        value = "+typ+"(value)\n"
                  +pad+"    return super().insert(index, value)\n\n")
            changes.append((owner.end_lineno+1,code))
        if "__setitem__" in entry:
            m=ms.get("__setitem__")
            if not m or len(m.args.args)<3:raise ValueError("UNKNOWN_ASSIGNMENT_ARITY")
            key,val=m.args.args[1].arg,m.args.args[2].arg
            body=(f"if isinstance({key}, slice):\n"
                  f"    {val} = [{typ}(v) if isinstance(v, {guard}) and not isinstance(v, {typ}) else v for v in {val}]\n")
            pad=" "*m.body[-1].col_offset
            changes.append((start(m),"".join(pad+l+"\n" for l in body.rstrip().splitlines())))
        return insert_lines(src,changes),{"rule":"source-sibling-normalization","native_converter":typ,"typed_guard":guard,"insertions":len(changes)}
    if "__delitem__" in entry and len(entry["__delitem__"])>=2:
        helper=ms.get(entry["__delitem__"][-1])
        if not helper or len(helper.args.args)<4:raise ValueError("UNKNOWN_SLICE_HELPER")
        ctor=ms.get("__init__");fields=set()
        for n in ast.walk(ctor):
            if isinstance(n,ast.Assign) and isinstance(n.value,ast.List) and len(n.value.elts)==1 and isinstance(n.value.elts[0],ast.List) and not n.value.elts[0].elts:
                for t in n.targets:
                    if isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id==ctor.args.args[0].arg:fields.add(t.attr)
        if len(fields)!=1:raise ValueError("UNKNOWN_BACKING_REPRESENTATION")
        field=fields.pop()
        if not any(isinstance(n,ast.Subscript) and isinstance(n.value,ast.Attribute) and n.value.attr==field for m in ms.values() for n in ast.walk(m)):
            raise ValueError("UNKNOWN_NO_SOURCE_REBUILD_EVIDENCE")
        rebalancers=[m for m in ms if "balance" in m.lower()]
        if len(rebalancers)!=1:raise ValueError("UNKNOWN_BALANCER")
        recv,a,b,c=[x.arg for x in helper.args.args[:4]]
        body=(f"_mg_snapshot = list({recv})\n"
              f"del _mg_snapshot[slice({a}, {b}, {c})]\n"
              f"{recv}.{field}[:] = [_mg_snapshot]\n"
              f"{recv}.{rebalancers[0]}(0)\n"
              "return\n")
        pad=" "*helper.body[-1].col_offset
        return insert_lines(src,[(start(helper),"".join(pad+x+"\n" for x in body.rstrip().splitlines()))]),{"rule":"source-projected-list-snapshot","source_field":field,"method":helper.name}
    raise ValueError("UNKNOWN_NO_SOURCE_ATTESTED_REPAIR")

def test_existing(tree,cand):
    tests=[]
    for root in ("tests","test"):
        d=tree/root
        if d.exists():
            for p in d.rglob("test*.py"):
                try:
                    if cand["class"] in p.read_text():tests.append(str(p))
                except Exception:pass
    if not tests:return {"status":"UNKNOWN_NO_NAMED_ORIGINAL_TEST"}
    selected=sorted(tests)[:4]
    env=dict(os.environ,PYTHONPATH=os.pathsep.join([str(tree/"src"),str(tree)]))
    begun=time.monotonic()
    try:
        p=subprocess.run([sys.executable,"-m","pytest","-q",*selected],cwd=tree,env=env,text=True,capture_output=True,timeout=185)
    except subprocess.TimeoutExpired:
        return {"status":"UNKNOWN_TEST_TIMEOUT","files":selected}
    m=re.findall(r"(\d+) passed",p.stdout+p.stderr)
    n=int(m[-1]) if m else 0
    return {"status":"PASS" if p.returncode==0 and n>0 else "FAIL",
            "passed":n,"exit":p.returncode,"files":selected,
            "seconds":round(time.monotonic()-begun,3),
            "stdout_tail":p.stdout[-1600:],"stderr_tail":p.stderr[-700:]}

def keys(x):
    return {(p["law"],p["family"],p["slice"]) for p in x.get("program_keys",[]) if p["status"]=="VIOLATION"}
def run_one(target,root,out):
    try:
        repo,trees=prior.make_worktrees(root,target)
        results=[]
        for c in seq.source_candidates(repo,trees,target):
            before=seq.replay(trees["base"],c,target["base"])
            author=seq.replay(trees["head"],c,target["head"])
            if not keys(before) or keys(author):
                results.append({"status":"UNKNOWN_UNSUPPORTED_ORIGINAL_WITNESS"});continue
            path=trees["base"]/c["file"]
            original=path.read_bytes()
            try: proposed,rule=mk(original.decode("utf-8"),c)
            except Exception as e:
                results.append({"status":"UNKNOWN_GRAMMAR","reason":str(e)});continue
            raw=proposed.encode()
            patch="".join(difflib.unified_diff(original.decode().splitlines(keepends=True),proposed.splitlines(keepends=True),
                                                fromfile="a/"+c["file"],tofile="b/"+c["file"]))
            patchpath=out/(target["repo"].replace("/","_")+".patch")
            patchpath.write_text(patch)
            try:
                path.write_bytes(raw)
                after=seq.replay(trees["base"],c,target["base"])
                suite=test_existing(trees["base"],c)
            finally:path.write_bytes(original)
            removed=seq.replay(trees["base"],c,target["base"])
            restored=path.read_bytes()==original
            fixed=len(keys(before)-keys(after));new=len(keys(after)-keys(before))
            ablated=keys(removed)==keys(before)
            qualified=bool(fixed>0 and not keys(after) and new==0 and suite["status"]=="PASS" and ablated and restored)
            results.append({"status":"WARRANTED_BOUNDED_REPAIR_INSTANCE" if qualified else "UNKNOWN_OR_REJECTED_REPAIR",
                            "qualified":qualified,"source_candidate":c,"rule":rule,
                            "native_fixed":fixed,"native_new_failures":new,"native_remaining":len(keys(after)),
                            "baseline_old_failures":len(keys(before)),"native_suite":suite,
                            "physical_ablation_reinstates_original":ablated,
                            "original_bytes_restored":restored,
                            "patch_sha256":prior.sha_file(patchpath),
                            "original_sha256":hashlib.sha256(original).hexdigest(),
                            "patched_sha256":hashlib.sha256(raw).hexdigest()})
        return {"repo":target["repo"],"qualified":any(x.get("qualified") for x in results),"trials":results}
    except Exception as exc:
        return {"repo":target["repo"],"qualified":False,"status":"UNKNOWN_HARNESS","reason":type(exc).__name__+":"+str(exc)[:300]}
def main():
    out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "evidence");out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        results=[run_one(t,pathlib.Path(td)/("subject"+str(i)),out) for i,t in enumerate(seq.TARGETS)]
    verdict=("WARRANTED_BOUNDED_TWO_SOURCE_DERIVED_SEQUENCE_REPAIRS" if all(x["qualified"] for x in results) else "UNKNOWN_OR_REJECTED_SEQUENCE_REPAIRS")
    report={"status":verdict,"results":results,"human_designed_repair_grammar":True,"scientific_L7":"UNKNOWN",
            "strong_equal_information_agent_baseline":"NOT_RUN",
            "protocol_sha256":prior.sha_file(HERE/"FROZEN_REPAIR_PROTOCOL.md"),
            "source_sha256":prior.sha_file(__file__),"external_repo_writes":0}
    path=out/"repair_report.json";path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":verdict,"report_sha256":prior.sha_file(path),"results":[{"repo":x["repo"],"qualified":x["qualified"],
                       "details":[{"status":y["status"],"rule":y.get("rule"),"fixed":y.get("native_fixed"),
                                   "suite":y.get("native_suite",{}).get("status"),"tests":y.get("native_suite",{}).get("passed")}
                                  for y in x.get("trials",[])]} for x in results],"L7":"UNKNOWN"},sort_keys=True))
    return 0 if all(x["qualified"] for x in results) else 1
if __name__=="__main__":raise SystemExit(main())
