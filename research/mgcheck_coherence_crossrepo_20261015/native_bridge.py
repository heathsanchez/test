#!/usr/bin/env python3
"""Frozen 16-program native common TOML interface bridge. No repo-specific method code."""
from __future__ import annotations
import hashlib, importlib, inspect, json, pathlib, subprocess, sys, time, tomllib, traceback

def canonical(x):
    if isinstance(x, dict): return ["mapping", [[str(k), canonical(v)] for k,v in sorted(x.items(),key=lambda kv:str(kv[0]))]]
    if isinstance(x, (list,tuple)): return ["sequence", [canonical(v) for v in x]]
    if isinstance(x, bool): return ["bool",x]
    if isinstance(x, int): return ["integer",x]
    if isinstance(x, float): return ["float",repr(x)]
    if isinstance(x, str): return ["string",x]
    if x is None: return ["none"]
    return ["unsupported",type(x).__name__]

def corpus():
    # FROZEN common typed grammar — independent of source authors' exact literals.
    v=[]
    for i,val in enumerate([0.0,10.0,-2.5,1000.25]):
        v.append({"value":val,"label":"batch-"+str(i),"enabled":(i%2==0)})
    for i, val in enumerate([1.0,2.5,-4.0,0.0]):
        v.append({"meta":{"cost":val,"code":i},"items":[3,2,1],"visible":True})
    for i in range(4):
        v.append({"groups":[
            {"name":"left-"+str(i),"nodes":[{"weight":2.0,"id":"m"},{"weight":3.0,"id":"n"}]},
            {"name":"right-"+str(i),"nodes":[{"weight":5.0,"id":"r"},{"weight":7.0,"id":"s"}]}
        ],"root_cost":i+0.5})
    for i in range(4):
        v.append({"source":"fixture-"+str(i),"units":[
            {"tag":"branch-a","details":[{"name":"p","quota":10.0},{"name":"q","quota":20.0}]},
            {"tag":"branch-b","details":[{"name":"r","quota":30.0}]}
        ],"independent":{"enabled":True,"count":i}})
    assert len(v)==16
    return v

def load_module(root):
    root=pathlib.Path(root).resolve()
    module_names=[f.stem for f in root.glob("*.py") if f.name not in ("setup.py","conftest.py") and not f.name.startswith("test")]
    module_names += [d.name for d in root.iterdir() if d.is_dir() and (d/"__init__.py").exists() and not d.name.startswith("test")]
    sys.path.insert(0,str(root))
    errors=[]
    for name in sorted(set(module_names)):
        try:
            m=importlib.import_module(name)
            origin=pathlib.Path(getattr(m,"__file__","")).resolve()
            if root not in origin.parents: continue
            if callable(getattr(m,"loads",None)) and callable(getattr(m,"dumps",None)):
                return name,m
        except Exception as e:
            errors.append({"candidate":name,"exception":str(e)})
    raise RuntimeError("UNKNOWN_NATIVE_INTERFACE; no common loads/dumps; candidates="+repr(module_names)+" import_errors="+repr(errors))

def main():
    if len(sys.argv)!=5:
        raise SystemExit("usage: native_bridge.py SOURCE_TREE REPO_ID REV_ID EVIDENCE_DIR")
    root, repo, rev, out=map(str,sys.argv[1:])
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    t0=time.perf_counter_ns()
    sha=subprocess.check_output(["git","-C",root,"rev-parse","HEAD"],text=True).strip()
    name,m=load_module(root)
    sig=inspect.signature(m.dumps)
    mode_names=["default"]+(["sort_keys"] if "sort_keys" in sig.parameters else [])
    rows=[];native_calls=0;ref_calls=0;own_calls=0
    for i, data in enumerate(corpus()):
        for mode in mode_names:
            kw={} if mode=="default" else {"sort_keys":True}
            row={"program_index":i,"mode":mode,"input_canonical":canonical(data)}
            try:
                ts=time.perf_counter_ns()
                rendered=m.dumps(data,**kw)
                native_calls+=1
                row["native_us"]=(time.perf_counter_ns()-ts)//1000
                row["render_sha256"]=hashlib.sha256(rendered.encode()).hexdigest()
                row["render_len"]=len(rendered)
                row["native_status"]="OK"
                try:
                    reference=tomllib.loads(rendered)
                    ref_calls+=1
                    row["reference_canonical"]=canonical(reference)
                    row["coherence"]="MATCH" if canonical(reference)==canonical(data) else "VIOLATION"
                except Exception as e:
                    ref_calls+=1
                    row["coherence"]="UNKNOWN_REFERENCE_REJECTED"
                    row["reference_error"]=str(e)[:400]
                try:
                    own=m.loads(rendered);own_calls+=1
                    row["own_reparse_equal"]=canonical(own)==canonical(data)
                except Exception as e:
                    own_calls+=1
                    row["own_reparse_error"]=str(e)[:400]
            except Exception as e:
                native_calls+=1
                row["native_status"]="UNKNOWN_NATIVE_EXCEPTION"
                row["native_error"]=type(e).__name__+": "+str(e)[:400]
                row["coherence"]="UNKNOWN_NATIVE_EXCEPTION"
            rows.append(row)
    report={"repo":repo,"rev":rev,"source_sha":sha,"discovered_module":name,
        "selected_methods":["loads","dumps"],"supported_modes":mode_names,
        "corpus_size":16,"calls":{"native_dumps":native_calls,"reference_parse":ref_calls,"own_parse":own_calls},
        "elapsed_ns":time.perf_counter_ns()-t0,"results":rows}
    path=out/(repo+"_"+rev+".json")
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"repo":repo,"rev":rev,"source_sha":sha,"module":name,
        "modes":mode_names,"calls":report["calls"],"outcomes":{k:sum(r["coherence"]==k for r in rows) for k in sorted(set(r["coherence"] for r in rows))},"elapsed_ns":report["elapsed_ns"]}))
if __name__=="__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"status":"UNKNOWN_NATIVE_APPARATUS","error":type(e).__name__+": "+str(e),"traceback":traceback.format_exc()[-1600:]}))
        raise
