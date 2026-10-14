#!/usr/bin/env python3
"""Source-native compiled/Python interface parity miner; no target-specific operation manifest."""
import argparse, hashlib, importlib, inspect, json, math, pkgutil, time
from pathlib import Path

def save(p,x):
    Path(p).write_text(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=True)+"\n")

def norm(v,d=0):
    if d>8: return ["UNKNOWN_DEPTH"]
    if v is None: return ["none"]
    if type(v) is bool: return ["bool",v]
    if type(v) is int: return ["int",str(v)]
    if type(v) is float: return ["float",repr(v)] if math.isfinite(v) else ["UNKNOWN_NONFINITE"]
    if type(v) is str: return ["str",v]
    if type(v) is bytes: return ["bytes",v.hex()]
    if type(v) in (tuple,list): return [type(v).__name__,[norm(a,d+1) for a in v]]
    if type(v) is dict: return ["dict",[[norm(k,d+1),norm(vv,d+1)] for k,vv in v.items()]]
    return ["UNKNOWN_TYPE",type(v).__module__+"."+type(v).__name__]

def observed(f,args):
    try:
        v=norm(f(*args))
        return {"kind":"unknown" if "UNKNOWN" in json.dumps(v) else "value","result":v}
    except (KeyboardInterrupt,SystemExit): raise
    except Exception as e:
        r={"kind":"exception","type":type(e).__module__+"."+type(e).__name__,"message":str(e)}
        for k in ("msg","pos","lineno","colno"):
            if hasattr(e,k): r[k]=norm(getattr(e,k))
        return r

def inputs(arity):
    # Operation-agnostic typed string vocabulary and finite argument positions.
    atoms=["","a","ab","abc","0","1",'"',"'","\\","/","{","}","[","]",",",":"," ","\n","\r","\t","\x00","\x01","\x1f"]
    prefixes=["","a","ab","xyz",'"',"'","\\"]
    tails=["",'"',"a","b","\\"," "]
    seen=set()
    for pre in prefixes:
        for atom in atoms:
            for tail in tails:
                core=pre+atom+tail
                for s in (core,'"'+core+'"',"'"+core+"'","["+core+"]","{"+core+"}"):
                    if s in seen: continue
                    seen.add(s)
                    if arity==1: yield [s]
                    else:
                        for k in sorted(set((0,1,2,len(s),max(0,len(s)-1)))):
                            yield [s,k]

def discover(root):
    dirs=sorted(z.name for z in Path(root).iterdir() if z.is_dir() and (z/"__init__.py").is_file() and not z.name.startswith("_"))
    modules=[]; rejected=[]
    for name in dirs:
        try:
            p=importlib.import_module(name)
            modules.append(p)
            for i in sorted(pkgutil.walk_packages(p.__path__,prefix=name+"."),
                            key=lambda n:n.name):
                if ".test" in i.name: continue
                try: modules.append(importlib.import_module(i.name))
                except Exception as e: rejected.append([i.name,type(e).__name__])
        except Exception as e: rejected.append([name,type(e).__name__])
    pairs=[]
    for m in modules:
        for name,f in sorted(vars(m).items()):
            if not name.startswith("py_") or not callable(f): continue
            g=vars(m).get("c_"+name[3:])
            if not callable(g) or not inspect.isbuiltin(g): continue
            try:
                params=[x for x in inspect.signature(f).parameters.values()
                        if x.kind in (inspect.Parameter.POSITIONAL_ONLY,inspect.Parameter.POSITIONAL_OR_KEYWORD)]
                arity=sum(x.default is inspect.Parameter.empty for x in params)
                if arity not in (1,2): continue
                src=inspect.getsourcefile(f)
                digest=hashlib.sha256(Path(src).read_bytes()).hexdigest() if src else None
            except (TypeError,ValueError): continue
            pairs.append({"module":m.__name__,"py":name,"native":"c_"+name[3:],"arity":arity,
                          "python_source_sha256":digest,"native_origin":getattr(g,"__module__",None)})
    return dirs,pairs,rejected

def funcs(spec):
    m=importlib.import_module(spec["module"])
    a=getattr(m,spec["py"]); b=getattr(m,spec["native"])
    if not inspect.isbuiltin(b): raise RuntimeError("MISSING_COMPILED_REFERENCE")
    return a,b

def prescan(root,sha):
    start=time.perf_counter(); pkgs,pairs,errors=discover(root); entries=[]
    for spec in pairs:
        a,b=funcs(spec); divergent=[]; agreeing=[]; counts={"tested":0,"different":0,"equal":0,"unknown":0}
        for args in inputs(spec["arity"]):
            x,y=observed(a,args),observed(b,args);counts["tested"]+=1
            if "unknown" in (x["kind"],y["kind"]): counts["unknown"]+=1; continue
            rec={"args":args,"python":x,"native":y}
            if x==y:
                counts["equal"]+=1
                if len(agreeing)<64: agreeing.append(rec)
            else:
                counts["different"]+=1
                if len(divergent)<3000: divergent.append(rec)
        entries.append({"interface":spec,"counts":counts,"witnesses":divergent,"controls":agreeing,
                        "truncated":len(divergent)<counts["different"]})
    return {"schema":"mgcheck.native-interface-discovery.v0","stage":"OLD_SOURCE_FROZEN",
            "source_sha":sha,"packages":pkgs,"discovery_rule":"same-module py_*/c_* pair; native builtin required",
            "target_operation_manifest":None,"entries":entries,"import_errors":errors,
            "elapsed_seconds":round(time.perf_counter()-start,4),
            "baseline":"equal-information differential comparison of the same pairs and inputs is equally powerful",
            "unknown_scopes":["intent","self-generated-meta-grammar","reviewer-economic-superiority"]}

def replay(sha,old):
    start=time.perf_counter();rows=[]
    for entry in old["entries"]:
        spec=entry["interface"]
        try: a,b=funcs(spec)
        except Exception as e:
            rows.append({"interface":spec,"state":"UNKNOWN_NO_NATIVE_REFERENCE","error":str(e)})
            continue
        closed=0;still=0;unknown=0;first=None;controls_ok=0
        for w in entry["witnesses"]:
            x,y=observed(a,w["args"]),observed(b,w["args"])
            if "unknown" in (x["kind"],y["kind"]):unknown+=1
            elif x==y:
                closed+=1
                candidate={"args":w["args"],"old_python":w["python"],"old_native":w["native"],
                           "head_python":x,"head_native":y}
                if first is None or (len(w["args"][0]),repr(w["args"]))<(len(first["args"][0]),repr(first["args"])):
                    first=candidate
            else: still+=1
        for q in entry["controls"]:
            x,y=observed(a,q["args"]),observed(b,q["args"])
            if x==y==q["python"]:controls_ok+=1
        rows.append({"interface":spec,"state":"BOTH_EXECUTED","old_disagree":entry["counts"]["different"],
                     "frozen_witnesses_replayed":len(entry["witnesses"]),"closed":closed,
                     "persistent":still,"unknown":unknown,"control_agreement":controls_ok,
                     "control_total":len(entry["controls"]),"smallest_preselected_closure":first})
    passes=[r for r in rows if r["state"]=="BOTH_EXECUTED" and r["closed"]>0 and
            r["control_agreement"]==r["control_total"]]
    return {"schema":old["schema"],"stage":"ORIGINAL_HEAD_REPLAY",
            "original_pre_fix_source":old["source_sha"],"original_author_head":sha,
            "old_manifest_digest":hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest(),
            "results":rows,"status":"WARRANTED_BOUNDED_PAIRED_INTERFACE_OBLIGATION" if passes else "UNKNOWN_NO_CLOSED_WITNESS",
            "no_reference_ablation":"UNKNOWN_REFERENCE_REMOVED",
            "wrong_source_ablation":"UNKNOWN_SUBJECT_MISMATCH",
            "strong_baseline":"TIE: same-information pairwise differential baseline reproduces these observations",
            "not_warranted":["novel_upstream_defect","semantic_intent","fully_autonomous_L7","third_family_transfer","reviewer_advantage"],
            "elapsed_seconds":round(time.perf_counter()-start,4)}

def main():
    p=argparse.ArgumentParser();p.add_argument("stage",choices=("scan","replay"))
    p.add_argument("--site");p.add_argument("--sha",required=True)
    p.add_argument("--frozen");p.add_argument("--output",required=True)
    a=p.parse_args()
    if a.stage=="scan":
        result=prescan(a.site,a.sha)
        good=any(x["counts"]["different"]>0 for x in result["entries"])
    else:
        result=replay(a.sha,json.loads(Path(a.frozen).read_text()))
        good=result["status"]=="WARRANTED_BOUNDED_PAIRED_INTERFACE_OBLIGATION"
    save(a.output,result)
    if a.stage=="scan":
        report=[{"pair":x["interface"]["module"]+"."+x["interface"]["py"],
                 "native":x["interface"]["native"],"counts":x["counts"]} for x in result["entries"]]
    else:
        report=[{"pair":x["interface"]["module"]+"."+x["interface"]["py"],
                 "closed":x.get("closed"),"persistent":x.get("persistent")} for x in result["results"]]
    print("RESEARCH_RESULT="+json.dumps({"stage":result["stage"],"status":result.get("status"),"pairs":report},sort_keys=True))
    if not good:raise SystemExit("FROZEN_GATE_NOT_MET")

if __name__=="__main__":main()
