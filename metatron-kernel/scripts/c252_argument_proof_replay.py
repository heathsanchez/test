"""C252: direct exact verified argument typing at zero fuel after C247+C250+C251.

Only a fresh, full source-typed argument check can give a Proven result at
original zero fuel. The C251 Pi view and original function type remain
source-authenticated. This is opt-in bounded resource policy only.
"""
import argparse,hashlib,json,os,pathlib,subprocess,time,zipfile
ARCHIVE="5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED="e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
TERM="NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"
FLAG="NUCLEUS_C252_ARGUMENT_PROOF_RETRY"
EXTRAS=("C182_TYPED_PROOF_IRREL","C189_NEUTRAL_LAMBDA_PROOF",
        "C190_QUOTIENT_IOTA","C199_TWO_PARAM_EIGHT_FIELD_RECORD",
        "C201_CLOSED_NULLARY_ENUM","C216_RIGID_DATA_FUNCTION_CTOR")
CONTROLS=("bad/bugs/eta-ctor-alias.ndjson",
          "bad/bugs/rec-rule-proof-irrel.ndjson",
          "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
          "bad/bugs/rec-type-proof-irrel.ndjson",
          "bad/bugs/rec-rule-wrong-arg.ndjson",
          "bad/bugs/closure-level-subst.ndjson",
          "bad/bugs/constlevels.ndjson",
          "bad/bugs/pi-closure-context.ndjson",
          "bad/bugs/loose-bvar-value.ndjson",
          "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
          "good/tutorial/126_quotMkType.ndjson")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def replay(checker,raw,env,path,label,timeout=180):
    start=time.monotonic()
    p=subprocess.run([str(checker)],input=raw,env=env,capture_output=True,timeout=timeout,check=False)
    log=p.stderr.decode(errors="replace")
    (path/(label+".stderr")).write_text(log)
    direct=[l for l in log.splitlines() if l.startswith("NUCLEUS_C252_ARG_RETRY:")]
    end=[l for l in log.splitlines() if l.startswith("NUCLEUS_DOWNSTREAM:")]
    return {"case":label,"exit":p.returncode,"elapsed_s":round(time.monotonic()-start,3),
            "source_sha256":sha(raw),"argument_retry_events":len(direct),
            "last_retry_events":direct[-8:],"terminal":end[-1:]}

def main():
    p=argparse.ArgumentParser()
    for key in ("archive","checker","flags","out"):p.add_argument("--"+key,required=True,type=pathlib.Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if sha(a.archive.read_bytes())!=ARCHIVE:raise ValueError("Original archive SHA mismatch")
    historical=json.loads(a.flags.read_text())["flags"]
    if len(historical)!=24 or set(historical.values())!={"1"}:
        raise ValueError("Historical flags mismatch")
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(historical);base.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    base["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"]="1"
    base["NUCLEUS_C247_TYPED_PI_LOCAL_RETRY"]="1"
    base["NUCLEUS_C250_ZERO_DOMAIN_RETRY"]="1"
    base["NUCLEUS_C251_LITERAL_PI_VIEW"]="1"
    base["NUCLEUS_TRACE_DOWNSTREAM"]="1"
    base["NUCLEUS_C225_JUDGMENT_STEPS"]="69632"
    with zipfile.ZipFile(a.archive) as z:
        original={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(original)!=212:raise ValueError("Wrong source count")
        def source(case):
            blob=z.read("inputs/"+case)
            if sha(blob)!=original[case]["sha256"]:raise ValueError("Source drift: "+case)
            return blob
        fueled=source("good/perf/fueled-chain.ndjson")
        if sha(fueled)!=FUELED:raise ValueError("Wrong Fueled export")
        observations=[]
        for lexical in (False,True):
            for direct in (False,True):
                env=base.copy()
                if lexical:env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                if direct:
                    env[FLAG]="1"
                    env["NUCLEUS_C252_TRACE"]="1"
                row=replay(a.checker,fueled,env,a.out,f"fueled_lex{int(lexical)}_pi{int(direct)}")
                row["lexical"]=lexical;row["direct"]=direct
                if row["exit"] not in (0,2):raise ValueError("Incorrect original verdict: "+str(row))
                if not direct and row["exit"]!=2:raise ValueError("Original baseline changed: "+str(row))
                if row["exit"]==2 and row["terminal"]!=[TERM]:
                    raise ValueError("Unexpected original terminal: "+str(row))
                observations.append(row)
                print("C252_FUELED",json.dumps(row,sort_keys=True),flush=True)
        controls=[]
        for case in CONTROLS:
            b=source(case)
            for direct in (False,True):
                env=base.copy()
                env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                if direct:env[FLAG]="1"
                row=replay(a.checker,b,env,a.out,
                           "control_"+case.replace("/","_").removesuffix(".ndjson")+f"_pi{int(direct)}",timeout=90)
                row["original"]=case;row["direct"]=direct
                if row["exit"]!=original[case]["actual"] or row["exit"]!=original[case]["expected"]:
                    raise ValueError("Protected control drift: "+str(row))
                controls.append(row)
        if len(controls)!=2*len(CONTROLS):raise ValueError("Missing control")
    gains=[r for r in observations if r["direct"] and r["exit"]==0]
    report={"status":"WARRANTED_BOUNDED_IF_GITHUB_SUCCESS",
            "source_archive_sha256":ARCHIVE,"fueled_source_sha256":FUELED,
            "experiment":"Source-typed original argument check after C247+C250+C251 proof path",
            "whole_fueled_positive":bool(gains),"original":observations,"protected":controls}
    (a.out/"c252-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C252_SUMMARY",json.dumps({"original":[(r["lexical"],r["direct"],r["exit"],r["argument_retry_events"]) for r in observations],
            "controls":[r["exit"] for r in controls],"whole_fueled_positive":bool(gains)},sort_keys=True),flush=True)
if __name__=="__main__":main()
