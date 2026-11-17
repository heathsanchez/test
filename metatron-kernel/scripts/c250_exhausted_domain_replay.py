"""C250: independently proved, 16-step local domain retry at exhausted fuel.

All 212 original Lean Arena exports are SHA-pinned; the checker must never
emit incorrect ACCEPT/REJECT, crash, or retract a historical decisive result.
The only candidate rule schedules the SAME real independent conversion under
the SAME protected source context after original fuel reaches zero. It may
return a proof or leave UNKNOWN; it is never a shortcut equality.
"""
import argparse,hashlib,json,os,pathlib,subprocess,time,zipfile

ARCHIVE = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
EXTRAS=("C182_TYPED_PROOF_IRREL","C189_NEUTRAL_LAMBDA_PROOF",
        "C190_QUOTIENT_IOTA","C199_TWO_PARAM_EIGHT_FIELD_RECORD",
        "C201_CLOSED_NULLARY_ENUM","C216_RIGID_DATA_FUNCTION_CTOR")
SIX=("good/perf/fueled-chain.ndjson","good/perf/grind-ring-5.ndjson",
     "good/perf/magma-list-deep-n21.ndjson","good/perf/magma-list-deep-n36.ndjson",
     "good/perf/magma-list-pair-n21.ndjson","good/perf/magma-list-pair-n7.ndjson")
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

def sha(raw): return hashlib.sha256(raw).hexdigest()
def replay(checker, raw, env, folder, name, timeout=240):
    start=time.monotonic()
    try:
        p=subprocess.run([str(checker)],input=raw,env=env,
                         capture_output=True,timeout=timeout,check=False)
        rc=p.returncode
        log=p.stderr.decode(errors="replace")
    except subprocess.TimeoutExpired as e:
        rc=124
        log=(e.stderr or b"").decode(errors="replace")
    (folder/(name+".stderr")).write_text(log)
    events=[x for x in log.splitlines() if x.startswith("NUCLEUS_C250_DOMAIN_RETRY:")]
    c247=[x for x in log.splitlines() if x.startswith("NUCLEUS_C247_CONVERSION_RETRY:")]
    term=[x for x in log.splitlines() if x.startswith("NUCLEUS_DOWNSTREAM:")]
    return {"label":name,"exit":rc,"secs":round(time.monotonic()-start,3),
            "source_sha256":sha(raw),
            "retry_count":len(events),
            "retry_proven":sum("candidate=Proven" in s for s in events),
            "retry_events":events[:20],
            "c247_proven":sum("candidate=Proven" in s for s in c247),
            "last_downstream":term[-1:]}

def main():
    p=argparse.ArgumentParser()
    for key in ("archive","checker","flags","out"):
        p.add_argument("--"+key,required=True,type=pathlib.Path)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    if sha(a.archive.read_bytes()) != ARCHIVE:
        raise ValueError("Original archive SHA-256 mismatch")
    flags=json.loads(a.flags.read_text())["flags"]
    if len(flags)!=24 or set(flags.values())!={"1"}:
        raise ValueError("Historical 24 flags changed")
    base={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    base.update(flags)
    base.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    base.update({"NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE":"1",
                 "NUCLEUS_C225_JUDGMENT_STEPS":"69632",
                 "NUCLEUS_C247_TYPED_PI_LOCAL_RETRY":"1",
                 "NUCLEUS_TRACE_DOWNSTREAM":"1"})
    with zipfile.ZipFile(a.archive) as archive:
        old={r["case"]:r for r in json.loads(archive.read("current212.json"))}
        if len(old)!=212:raise ValueError("Wrong source population")
        def source(case):
            b=archive.read("inputs/"+case)
            if sha(b)!=old[case]["sha256"]:
                raise ValueError("Source hash mismatch: "+case)
            return b
        fueled=source("good/perf/fueled-chain.ndjson")
        if sha(fueled)!=FUELED:raise ValueError("Wrong genuine Fueled source")
        paired=[]
        for lexical in (False,True):
            for candidate in (False,True):
                env=base.copy()
                if lexical: env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                if candidate:
                    env["NUCLEUS_C250_ZERO_DOMAIN_RETRY"]="1"
                    env["NUCLEUS_C250_TRACE"]="1"
                    env["NUCLEUS_C247_TRACE"]="1"
                row=replay(a.checker,fueled,env,a.out,f"fueled_lex{int(lexical)}_candidate{int(candidate)}")
                row.update(original="good/perf/fueled-chain.ndjson",lexical=lexical,candidate=candidate)
                if row["exit"] not in (0,2):
                    raise ValueError("Wrong/crashed original Fueled: "+str(row))
                if not candidate and row["exit"]!=2:
                    raise ValueError("Original Fueled baseline changed: "+str(row))
                paired.append(row)
                print("C250_FUELED",json.dumps(row,sort_keys=True),flush=True)
        protected=[]
        for case in CONTROLS:
            raw=source(case)
            for candidate in (False,True):
                env=base.copy()
                env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                if candidate:
                    env["NUCLEUS_C250_ZERO_DOMAIN_RETRY"]="1"
                    env["NUCLEUS_C250_TRACE"]="1"
                row=replay(a.checker,raw,env,a.out,
                    "control_"+case.replace("/","_").removesuffix(".ndjson")+
                    f"_candidate{int(candidate)}",timeout=60)
                row["original"]=case;row["candidate"]=candidate
                if row["exit"]!=old[case]["actual"] or row["exit"]!=old[case]["expected"]:
                    raise ValueError("Protected control changed: "+str(row))
                protected.append(row)
        if len(protected)!=22:raise ValueError("Incomplete protected paired replay")
        allrows=[]
        for i,case in enumerate(sorted(old)):
            if case=="good/perf/fueled-chain.ndjson":
                row=next(r for r in paired if r["lexical"] and r["candidate"])
            elif case in CONTROLS:
                row=next(r for r in protected if r["original"]==case and r["candidate"])
            else:
                env=base.copy()
                env["NUCLEUS_EXPERIMENTAL_C219_LEXICAL_ABSENCE"]="1"
                env["NUCLEUS_C250_ZERO_DOMAIN_RETRY"]="1"
                row=replay(a.checker,source(case),env,a.out,
                    "full_"+case.replace("/","_").removesuffix(".ndjson"))
            row=dict(row, original=case, expected=old[case]["expected"],
                     historical=old[case]["actual"])
            if row["exit"] not in (0,1,2):
                raise ValueError("Crash or timeout in complete corpus: "+str(row))
            if row["exit"] in (0,1) and row["exit"]!=row["expected"]:
                raise ValueError("Incorrect decisive verdict: "+str(row))
            if row["historical"] in (0,1) and row["exit"]!=row["historical"]:
                raise ValueError("Historical decisive regression: "+str(row))
            if row["historical"]==2 and row["exit"] not in (0,2):
                raise ValueError("Invalid original UNKNOWN promotion: "+str(row))
            allrows.append(row)
            if i%24==0: print("C250_PROGRESS",i+1,"/212",flush=True)
        if len(allrows)!=212:raise ValueError("Incomplete source corpus")
    summary={"state":"WARRANTED_BOUNDED_ONLY_IF_GITHUB_GREEN",
             "source_archive_sha256":ARCHIVE,
             "original_source_sha256":FUELED,
             "correct_counts":{str(n):sum(x["exit"]==n for x in allrows) for n in (0,1,2)},
             "new_valid_accepts":[x["original"] for x in allrows if x["historical"]==2 and x["exit"]==0],
             "remaining_valid_unknowns":[x["original"] for x in allrows if x["exit"]==2],
             "all_212_checked":True,
             "no_wrong_or_crash":True,
             "fueled_modes":paired,
             "protected":protected,
             "allrows":allrows}
    (a.out/"c250-complete.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("C250_SUMMARY",json.dumps({k:v for k,v in summary.items() if k not in ("allrows","protected")},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
