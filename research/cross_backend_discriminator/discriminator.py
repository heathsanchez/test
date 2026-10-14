#!/usr/bin/env python3
"""Small source-native *differential executor*, not a theorem prover or autonomous operator inventor.

No target/source-specific cases. All syntax and runner commands are in the
reviewable original-source manifest. Timeouts and runner errors are UNKNOWN.
Never turns a historical observation into permission to merge or act.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, os, pathlib, re, subprocess, time

MAX_CASES = 500
VARIABLE = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
def stable(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha(o): return hashlib.sha256(stable(o).encode()).hexdigest()
def require(v, why):
    if not v: raise ValueError(why)

def strings(alphabet,maxlen):
    alphabet=list(alphabet)
    require(0<=maxlen<=5 and len(alphabet)<=6 and all(isinstance(x,str) and len(x)==1 for x in alphabet),"UNSUPPORTED_STRING_GRAMMAR")
    return ["".join(x) for n in range(maxlen+1) for x in itertools.product(alphabet,repeat=n)]
def domain(axes):
    names=[a.get("name") for a in axes]
    require(len(names)==len(set(names)) and all(re.fullmatch(r"[a-z][a-z0-9_]*",n or "") for n in names),"DUPLICATE_OR_BAD_AXIS")
    pools=[]
    for a in axes:
        if a.get("type")=="strings":
            pools.append(strings(a.get("alphabet",[]),a.get("maxlen",0)))
        elif a.get("type")=="literals":
            require(0<len(a.get("values",[]))<=100,"BAD_LITERAL_DOMAIN")
            pools.append(a["values"])
        else: raise ValueError("UNKNOWN_INPUT_DOMAIN")
    count=1
    for p in pools: count*=len(p)
    require(count>0 and count<=MAX_CASES,"DOMAIN_BUDGET_EXCEEDED")
    return [dict(zip(names,x)) for x in itertools.product(*pools)]
def expand(template,params,bin_dir):
    require(isinstance(template,str),"INVALID_TEMPLATE")
    args={k:stable(v) for k,v in params.items()}
    args["BIN"]=str(bin_dir)
    def replace(m):
        name=m.group(1)
        require(name in args,"UNBOUND_TEMPLATE_PARAM_"+name)
        return args[name]
    return VARIABLE.sub(replace,template)

def evaluate(arm,prm,template,bin_dir,seconds):
    args=[expand(a,prm,bin_dir) for a in arm["argv"]]
    env=os.environ.copy()
    # Always run native external code as isolated CI processes, not in a networked
    # browser or privileged host. No secrets are supplied to the source programs.
    stdin=expand(template.get("stdin",""),prm,bin_dir)
    t0=time.perf_counter()
    try:
        z=subprocess.run(args,input=stdin,text=True,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=seconds,check=False,
            env={k:v for k,v in env.items() if k not in (
                "GITHUB_TOKEN","GH_PUBLIC_TOKEN","CLOUDFLARE_API_TOKEN",
                "MATHGRAPH_CHECK_APP_PRIVATE_KEY","GITHUB_APP_PRIVATE_KEY")})
        dt=time.perf_counter()-t0
        if z.returncode!=0:return dict(status="PROCESS_ERROR",exit=z.returncode,
            stdout_sha256=hashlib.sha256(z.stdout.encode()).hexdigest(),
            stderr_tail=z.stderr[-180:],seconds=round(dt,4))
        if template["normalization"]=="json":
            lines=[line for line in z.stdout.splitlines() if line.strip()]
            if len(lines)!=1:return dict(status="OUTPUT_COUNT_UNKNOWN",
                seconds=round(dt,4),line_count=len(lines))
            try: val=json.loads(lines[0])
            except json.JSONDecodeError:return dict(status="OUTPUT_PARSE_UNKNOWN",seconds=round(dt,4))
        elif template["normalization"]=="raw":
            lines=z.stdout.strip().splitlines()
            if len(lines)!=1:return dict(status="OUTPUT_COUNT_UNKNOWN",
                seconds=round(dt,4),line_count=len(lines))
            val=lines[0]
        else: raise ValueError("UNKNOWN_OUTPUT_NORMALIZATION")
        return dict(status="VALUE",value=val,seconds=round(dt,4))
    except subprocess.TimeoutExpired:
        return dict(status="TIMEOUT_UNKNOWN",seconds=seconds)
    except OSError:
        return dict(status="PROCESS_SETUP_UNKNOWN",seconds=round(time.perf_counter()-t0,4))

def comparison(a,b):
    if a.get("status")!="VALUE" or b.get("status")!="VALUE":
        return "UNKNOWN"
    return "EQUAL" if a["value"]==b["value"] else "DIFFERENT"
def valid_sources(manifest):
    for d in manifest["sources"]:
        p=pathlib.Path(d["local_dir"])
        z=subprocess.run(["git","rev-parse","HEAD"],cwd=p,text=True,capture_output=True,check=False,timeout=10)
        require(z.returncode==0 and z.stdout.strip()==d["sha"],"SOURCE_SHA_MISMATCH_"+d["name"])

def execute(manifest,bin_dir,ablate=None,withdraw=False):
    require(manifest.get("schema")=="metalogic.cross-implementation-native-domain.v1","WRONG_MANIFEST_SCHEMA")
    valid_sources(manifest)
    names=[a.get("name") for a in manifest["arms"]]
    require(names==["reference","base","head"],"WRONG_ARM_CONTRACT")
    if ablate is not None:require(ablate in names,"UNKNOWN_ABLATION_TARGET")
    cfg=manifest["expression"]
    observed=[]
    total_time=0.0
    for params in domain(manifest["axes"]):
        arms={}
        for a in manifest["arms"]:
            if ablate==a["name"]:arms[a["name"]]={"status":"ABLATION_UNAVAILABLE"}
            else:
                arms[a["name"]]=evaluate(a,params,cfg,bin_dir,float(manifest.get("timeout_seconds",2)))
                total_time+=arms[a["name"]].get("seconds",0)
        br=comparison(arms["base"],arms["reference"])
        hr=comparison(arms["head"],arms["reference"])
        observed.append({"input":params,"arms":arms,"base_reference":br,"head_reference":hr})
    diffs=[i for i in observed if i["base_reference"]=="DIFFERENT"]
    repaired=[i for i in diffs if i["head_reference"]=="EQUAL"]
    regressions=[i for i in observed if i["base_reference"]=="EQUAL" and i["head_reference"]=="DIFFERENT"]
    failures=[i for i in observed if i["base_reference"]=="DIFFERENT" and i["head_reference"]=="DIFFERENT"]
    unknowns=[i for i in observed if i["base_reference"]=="UNKNOWN" or i["head_reference"]=="UNKNOWN"]
    nonwitness=[i for i in observed if i["base_reference"]=="EQUAL" and i["head_reference"]=="EQUAL"]
    def minimum(rows):
        if not rows:return None
        x=min(rows,key=lambda r:(len(stable(r["input"])),stable(r["input"])))
        return {"input":x["input"],"reference":x["arms"]["reference"],
                "base":x["arms"]["base"],"head":x["arms"]["head"]}
    if withdraw: status="STALE_EVIDENCE_WITHDRAWN"
    elif ablate:status="UNKNOWN_REQUIRED_BACKEND_REMOVED"
    elif repaired and not regressions and not failures:status="WARRANTED_BOUNDED_NATIVE_DIFFERENTIAL_REPAIRED"
    elif diffs:status="REFUTED_BOUNDED_UNREPAIRED_OR_REGRESSED"
    else:status="UNKNOWN_NO_VALUE_MISMATCH_WITNESS"
    return {
      "schema":"metalogic.cross-implementation-native-consequence.v1",
      "family":manifest["name"],"sources":manifest["sources"],
      "generator":"HUMAN_WRITTEN_DECLARATIVE_DOMAIN_EXHAUSTION",
      "method_autonomously_invented":"NO",
      "domain_size":len(observed),
      "ablation":ablate,"withdrawal":withdraw,
      "result":status,
      "counts":{
        "base_reference_value_mismatches":len(diffs),
        "mismatches_repaired_at_head":len(repaired),
        "new_head_regressions":len(regressions),
        "unrepaired_base_differences":len(failures),
        "both_equal_controls":len(nonwitness),
        "timeouts_or_incomplete_evidence":len(unknowns)
      },
      "minimal_witness":minimum(repaired),
      "negative_control":minimum(nonwitness),
      "nonwitness_first":minimum(nonwitness),
      "machine_native_process_seconds_sum":round(total_time,3),
      "fully_informed_baseline":{
        "available_inputs":"EXACT SAME SOURCE_AND_TYPED_DOMAIN",
        "can_reproduce_same_witness":"YES",
        "reviewer_decision_superiority":"NOT_PROVEN",
        "human_time_or_dollar_savings":"NOT_MEASURED"
      },
      "action_authorization":"NONE",
      "nonclaims":[
        "No independent natural-language specification theorem",
        "Human authored manifests name operations and backend command syntax",
        "Only generated finite domain covered; TIMEOUT not a nontermination proof",
        "No outside-owner tool adoption",
        "No autonomous method-generator self-rewrite"
      ],
      "observations":observed
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--bin-dir",required=True)
    p.add_argument("--ablate",choices=["reference","base","head"])
    p.add_argument("--withdraw",action="store_true")
    a=p.parse_args()
    m=json.loads(pathlib.Path(a.manifest).read_text())
    r=execute(m,a.bin_dir,a.ablate,a.withdraw)
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("CROSS_IMPL "+json.dumps({
      "family":r["family"],"result":r["result"],
      "domain":r["domain_size"],"counts":r["counts"],
      "minimum":r["minimal_witness"]["input"] if r["minimal_witness"] else None,
      "baseline_win":"NOT_PROVEN"},ensure_ascii=False))
    if not a.ablate and not a.withdraw:
      require(r["result"]=="WARRANTED_BOUNDED_NATIVE_DIFFERENTIAL_REPAIRED",
          "NATIVE_DIFFERENTIAL_NOT_QUALIFIED")
