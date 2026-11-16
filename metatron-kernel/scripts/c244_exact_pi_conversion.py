"""C244 — original-dependent-Pi conversion contrast.

Observe identical, SHA-pinned original Fueled export in three separate
processes: certified C219 OFF, C219 ON, and C219 ON + non-authoritative
local conversion probes. Do not substitute diagnostic proofs into typing.
"""
import argparse, hashlib, json, os, pathlib, re, subprocess, time, zipfile
ARCHIVE="5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED="e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
TERM="NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"
EXTRAS=("C182_TYPED_PROOF_IRREL","C189_NEUTRAL_LAMBDA_PROOF",
        "C190_QUOTIENT_IOTA","C199_TWO_PARAM_EIGHT_FIELD_RECORD",
        "C201_CLOSED_NULLARY_ENUM","C216_RIGID_DATA_FUNCTION_CTOR")
CONTROLS=("bad/bugs/eta-ctor-alias.ndjson","bad/bugs/rec-rule-proof-irrel.ndjson",
          "bad/bugs/rec-rule-proof-irrel-nested.ndjson","bad/bugs/rec-type-proof-irrel.ndjson",
          "bad/bugs/rec-rule-wrong-arg.ndjson",
          "good/tutorial/119_reduceCtorParamRefl.mk.ndjson","good/tutorial/126_quotMkType.ndjson")
def sha(b): return hashlib.sha256(b).hexdigest()
def run(checker,raw,environment,out,label,timeout=180):
    start=time.monotonic()
    p=subprocess.run([str(checker)],input=raw,env=environment,
                     capture_output=True,timeout=timeout,check=False)
    log=p.stderr.decode(errors="replace")
    (out/(label+".stderr")).write_text(log)
    scopes=[x for x in log.splitlines() if x.startswith("NUCLEUS_C244_ORIGINAL:")]
    original=[x for x in log.splitlines() if x.startswith("NUCLEUS_C244_ORIGINAL_RESULT:")]
    local=[x for x in log.splitlines() if x.startswith("NUCLEUS_C244_LOCAL_PROBE:")]
    decisions=[x for x in log.splitlines() if x.startswith("NUCLEUS_C233_DECISION:")]
    source=[x for x in log.splitlines() if x.startswith("NUCLEUS_C244_SOURCE_PI:")]
    if len(scopes)!=len(original) or len(scopes)!=len(source):raise ValueError("Unpaired C244 events")
    return {"case":label, "exit":p.returncode,"secs":round(time.monotonic()-start,3),
            "sha256":sha(raw),"terminal_count":log.splitlines().count(TERM),
            "qualified_pi_target_count":len(scopes),
            "sampled_types":scopes[:8],
            "original_results":original[:12],
            "source_pi":source[:4],
            "probe_results":local[:64],
            "c233_decision_events":len(decisions),
            "decision_tail":decisions[-20:]}
def main():
    p=argparse.ArgumentParser()
    for key in ("archive","checker","flags","out"):p.add_argument("--"+key,required=True,type=pathlib.Path)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if sha(args.archive.read_bytes())!=ARCHIVE:raise ValueError("Original archive SHA mismatch")
    historical=json.loads(args.flags.read_text())["flags"]
    if len(historical)!=24 or set(historical.values())!={"1"}:raise ValueError("24 historical flags drift")
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(historical)
    base.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    base.update({"NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
                 "NUCLEUS_TRACE_DOWNSTREAM":"1",
                 "NUCLEUS_C225_JUDGMENT_STEPS":"69632"})
    with zipfile.ZipFile(args.archive) as z:
        old={r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(old)!=212: raise ValueError("Wrong source population")
        def source(case):
            b=z.read("inputs/"+case)
            if sha(b)!=old[case]["sha256"]:raise ValueError("Source changed: "+case)
            return b
        original=source("good/perf/fueled-chain.ndjson")
        if sha(original)!=FUELED:raise ValueError("Wrong Fueled source")
        compared=[]
        for mode in ("baseline","passive","probe"):
            env=base.copy()
            if mode!="baseline":
                env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                env["NUCLEUS_C244_PI_CONVERSION"]="1"
            if mode=="probe":env["NUCLEUS_C244_EXTRA_PROBES"]="1"
            row=run(args.checker,original,env,args.out,"fueled_"+mode)
            if row["exit"]!=2 or row["terminal_count"]!=1:
                raise ValueError("Unexpected original verdict: "+str(row)[:300])
            if mode!="baseline" and not row["qualified_pi_target_count"]:
                raise ValueError("Expected original Expr4782 source-dependent Pi was not reached")
            if mode=="probe" and not row["probe_results"]:
                raise ValueError("No diagnostic conversion probes")
            compared.append(row)
            print("C244_ORIGINAL",json.dumps(row,sort_keys=True),flush=True)
        protected=[]
        for case in CONTROLS:
            raw=source(case)
            for c219 in (False,True):
                env=base.copy()
                if c219:
                    env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                # Passive original diagnostic may sample no scope on control.
                env["NUCLEUS_C244_PI_CONVERSION"]="1"
                row=run(args.checker,raw,env,args.out,
                        "control_"+case.replace("/","_").removesuffix(".ndjson")+f"_c219{int(c219)}",
                        timeout=60)
                if row["exit"]!=old[case]["actual"] or row["exit"]!=old[case]["expected"]:
                    raise ValueError("Control regression: "+str(row)[:250])
                protected.append(row)
        if len(protected)!=14:raise ValueError("Missing controls")
    report={"status":"WARRANTED_BOUNDED_IF_GITHUB_GREEN",
            "source_archive_sha256":ARCHIVE,"fueled_source_sha256":FUELED,
            "original_verdict":"UNKNOWN",
            "source_provenance":"Original export unchanged; no new type/equality rule",
            "scope":"Under 24+6 flags, C234 reserve, and the explicitly isolated C219 lexical option",
            "original":compared,"protected":protected}
    (args.out/"c244-evidence.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C244_SUMMARY",json.dumps({"modes":[{"mode":x["case"],"exit":x["exit"],
                    "count":x["qualified_pi_target_count"],"probes":len(x["probe_results"])}
                for x in compared],
                "controls":[x["exit"] for x in protected]},sort_keys=True),flush=True)
if __name__=="__main__":main()
