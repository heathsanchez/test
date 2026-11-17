"""C248: exact source-owned argument domain after C247's local Pi proof.

Readonly probes on immutable 212-case source archive, in original Γ11.
No diagnostic result is substituted for an original verdict.
"""
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
def digest(raw):return hashlib.sha256(raw).hexdigest()
def replay(exe,raw,env,out,name):
    t=time.monotonic()
    run=subprocess.run([str(exe)],input=raw,env=env,capture_output=True,timeout=160,check=False)
    log=run.stderr.decode(errors="replace")
    (out/(name+".stderr")).write_text(log)
    source=[s for s in log.splitlines() if s.startswith("NUCLEUS_C248_SOURCE_DOMAIN:")]
    probes=[s for s in log.splitlines() if s.startswith("NUCLEUS_C248_DOMAIN_PROBE:")]
    c247=[s for s in log.splitlines() if s.startswith("NUCLEUS_C247_CONVERSION_RETRY:")]
    return {"case":name,"exit":run.returncode,"elapsed_s":round(time.monotonic()-t,3),
            "source_sha256":digest(raw),"terminal_count":log.splitlines().count(TERMINAL),
            "c247_positive_event":[s for s in c247 if "candidate=Proven" in s][:4],
            "domain_events":source[:8],"domain_probes":probes[:48],
            "domain_count":len(source)}
def main():
    p=argparse.ArgumentParser()
    for k in ("archive","checker","flags","out"):p.add_argument("--"+k,type=pathlib.Path,required=True)
    a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    if digest(a.archive.read_bytes())!=ARCHIVE:raise ValueError("Source archive changed")
    flags=json.loads(a.flags.read_text())["flags"]
    if len(flags)!=24 or set(flags.values())!={"1"}:raise ValueError("Flags changed")
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(flags)
    base.update({f"NUCLEUS_EXPERIMENTAL_{s}":"1" for s in EXTRAS})
    base.update({"NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
                 "NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE":"1",
                 "NUCLEUS_C225_JUDGMENT_STEPS":"69632",
                 "NUCLEUS_C247_TYPED_PI_LOCAL_RETRY":"1",
                 "NUCLEUS_C247_TRACE":"1",
                 "NUCLEUS_TRACE_DOWNSTREAM":"1"})
    with zipfile.ZipFile(a.archive) as z:
        corpus={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(corpus)!=212:raise ValueError("Corpus size changed")
        def source(key):
            raw=z.read("inputs/"+key)
            if digest(raw)!=corpus[key]["sha256"]:raise ValueError("Source changed: "+key)
            return raw
        fueled=source("good/perf/fueled-chain.ndjson")
        if digest(fueled)!=FUELED:raise ValueError("Fueled drift")
        rows=[]
        for mode in ("original","passive","probe"):
            env=base.copy()
            if mode!="original":env["NUCLEUS_C248_POSTRETRY_DOMAIN"]="1"
            if mode=="probe":env["NUCLEUS_C248_EXTRA_PROBES"]="1"
            row=replay(a.checker,fueled,env,a.out,"fueled_"+mode)
            if row["exit"]!=2 or row["terminal_count"]!=1:
                raise ValueError("Original verdict changed: "+str(row))
            if not row["c247_positive_event"]:raise ValueError("C247 source-local proof missing")
            if mode!="original" and not row["domain_events"]:
                raise ValueError("Missing original domain observer")
            if mode=="probe" and len(row["domain_probes"])<6:
                raise ValueError("Missing source-local conversion probes")
            rows.append(row)
            print("C248_ORIGINAL",json.dumps(row,sort_keys=True),flush=True)
        controls=[]
        for key in CONTROLS:
            env=base.copy();env["NUCLEUS_C248_POSTRETRY_DOMAIN"]="1"
            row=replay(a.checker,source(key),env,a.out,"control_"+key.replace("/","_").removesuffix(".ndjson"))
            if row["exit"] != corpus[key]["actual"] or row["exit"] != corpus[key]["expected"]:
                raise ValueError("Protected verdict changed: "+str(row))
            controls.append(row)
    result={"state":"WARRANTED_BOUNDED_IF_GITHUB_GREEN",
            "source_sha256":FUELED,"archive_sha256":ARCHIVE,
            "original_verdict":"UNKNOWN","read_only":True,
            "originals":rows,"controls":controls}
    (a.out/"c248-report.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("C248_SUMMARY",json.dumps({"exits":[r["exit"] for r in rows],
            "domain_count":[r["domain_count"] for r in rows],
            "domain_probes":rows[-1]["domain_probes"],
            "controls":[r["exit"] for r in controls]},sort_keys=True),flush=True)
if __name__=="__main__":main()
