"""C246: inspect actual bidirectional lambda proof path on unchanged source."""
import argparse,hashlib,json,os,pathlib,subprocess,time,zipfile
ARCHIVE="5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED="e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
TERMINAL="NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"
EXTRAS=("C182_TYPED_PROOF_IRREL","C189_NEUTRAL_LAMBDA_PROOF",
        "C190_QUOTIENT_IOTA","C199_TWO_PARAM_EIGHT_FIELD_RECORD",
        "C201_CLOSED_NULLARY_ENUM","C216_RIGID_DATA_FUNCTION_CTOR")
CONTROLS=("bad/bugs/eta-ctor-alias.ndjson","bad/bugs/rec-rule-proof-irrel.ndjson",
          "bad/bugs/rec-rule-proof-irrel-nested.ndjson","bad/bugs/rec-type-proof-irrel.ndjson",
          "bad/bugs/rec-rule-wrong-arg.ndjson",
          "good/tutorial/119_reduceCtorParamRefl.mk.ndjson","good/tutorial/126_quotMkType.ndjson")
def sha(x):return hashlib.sha256(x).hexdigest()
def run(exe,raw,env,out,name):
    start=time.monotonic()
    p=subprocess.run([str(exe)],input=raw,env=env,capture_output=True,timeout=180,check=False)
    stderr=p.stderr.decode(errors="replace")
    (out/(name+".stderr")).write_text(stderr)
    events=[l for l in stderr.splitlines() if l.startswith("NUCLEUS_C246_")]
    return {"name":name,"exit":p.returncode,"s":round(time.monotonic()-start,3),
            "sha256":sha(raw),"terminal":stderr.splitlines().count(TERMINAL),
            "events":events[:100], "events_count":len(events)}
def main():
    p=argparse.ArgumentParser()
    for k in ("archive","checker","flags","out"):p.add_argument("--"+k,type=pathlib.Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if sha(a.archive.read_bytes())!=ARCHIVE:raise ValueError("Archive drift")
    flags=json.loads(a.flags.read_text())["flags"]
    if len(flags)!=24 or set(flags.values())!={"1"}:raise ValueError("Flag drift")
    env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    env.update({"NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
                "NUCLEUS_C225_JUDGMENT_STEPS":"69632",
                "NUCLEUS_TRACE_DOWNSTREAM":"1"})
    with zipfile.ZipFile(a.archive) as z:
        original={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(original)!=212:raise ValueError("Corpus size drift")
        def source(case):
            raw=z.read("inputs/"+case)
            if sha(raw)!=original[case]["sha256"]:raise ValueError("Source drift "+case)
            return raw
        fueled=source("good/perf/fueled-chain.ndjson")
        if sha(fueled)!=FUELED:raise ValueError("Fueled drift")
        tests=[]
        for mode in ("unmodified","passive","probe"):
            selected=env.copy()
            if mode!="unmodified":
                selected["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                selected["NUCLEUS_C246_LAMBDA_PREMISES"]="1"
            if mode=="probe":selected["NUCLEUS_C246_BIDIR_PROBES"]="1"
            result=run(a.checker,fueled,selected,a.out,"fueled_"+mode)
            if result["exit"]!=2 or result["terminal"]!=1:raise ValueError("Original changed "+str(result))
            if mode!="unmodified" and not any("NUCLEUS_C246_LAMBDA_ENTER:" in x for x in result["events"]):
                raise ValueError("Target Expr4782 not reached")
            tests.append(result)
            print("C246_ORIGINAL",json.dumps(result,sort_keys=True),flush=True)
        controls=[]
        for case in CONTROLS:
            selected=env.copy()
            selected["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
            selected["NUCLEUS_C246_LAMBDA_PREMISES"]="1"
            result=run(a.checker,source(case),selected,a.out,
                "control_"+case.replace("/","_").removesuffix(".ndjson"))
            if result["exit"] not in (0,1) or result["exit"]!=original[case]["actual"] or result["exit"]!=original[case]["expected"]:
                raise ValueError("Wrong protected control "+str(result))
            controls.append(result)
    report={"state":"WARRANTED_BOUNDED_IF_GITHUB_GREEN","original_source_sha":FUELED,
            "unchanged_complete_verdict":"UNKNOWN","original":tests,"controls":controls}
    (a.out/"c246-report.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("C246_SUMMARY",json.dumps({
        "modes":[(q["name"],q["exit"],q["events_count"]) for q in tests],
        "controls":[q["exit"] for q in controls]},sort_keys=True),flush=True)
if __name__=="__main__":main()
