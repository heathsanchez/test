"""C84 exact source-expression + immutable captured Env node census.

All original inputs, source-qualified selected C58 reduction rules, and local
262144 standard allowances remain unchanged. Counters do not justify cache
reuse: pending application spine, source transparency and replay goal also
matter. Compare observer OFF/ON verdict, first C56 pair and C47 work counts.
"""
from pathlib import Path
import hashlib,json,os,re,subprocess

FLAGS=json.loads(Path("base/flags.json").read_text())
assert len(FLAGS)==24 and set(FLAGS.values())=={"1"}
CASES=[
    ("magma-list-pair-n7",8837,"abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
    ("magma-list-pair-n21",8827,"b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
]
Path("reports").mkdir(exist_ok=True)
rows=[]
keys=["outer_spent","outer_remaining","exposure_transitions","replay_reserved_units",
      "recursor_worklist_steps","conversion_pairs"]
for case,profile_expr,expected_hash in CASES:
    src=Path("arena207/good/perf/"+case+".ndjson").read_bytes()
    assert hashlib.sha256(src).hexdigest()==expected_hash
    observations=[]
    for enabled in [False,True]:
        env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(FLAGS)
        env.update({
            "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":str(profile_expr),
            "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
            "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
        })
        if enabled:env["NUCLEUS_C84_EXACT_CLOSURE_CENSUS"]="1"
        proc=subprocess.run(["candidate/nucleus-diagnostic","262144"],input=src,
                            capture_output=True,env=env,timeout=180)
        verdict={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}.get(proc.returncode,"ERROR")
        assert verdict=="UNKNOWN",(case,enabled,verdict)
        log=proc.stderr.decode(errors="replace").splitlines()
        works=[ln for ln in log if ln.startswith("NUCLEUS_C47_INNER_WORK:")]
        pairs=[ln for ln in log if ln.startswith("NUCLEUS_C56_PAIR:")]
        assert len(works)==1 and pairs,(case,enabled,len(works),len(pairs))
        work={k:int(re.search(k+r"=(\d+)",works[0]).group(1)) for k in keys}
        census=[ln for ln in log if ln.startswith("NUCLEUS_C84_CLOSURES:")]
        assert len(census)==int(enabled),(case,enabled,census)
        c84=json.loads(census[0].split(":",1)[1]) if enabled else None
        if enabled:
            assert c84["monitored_expr_ids_only"]
            assert c84["same_expr_env_does_not_imply_same_pending_spine_or_proof_goal"]
            assert c84["watch_transitions"]>=c84["unique_exact_expr_env_nodes"]
            assert c84["watch_transitions"]>=c84["exact_repeated_exposures"]
            assert c84["watch_transitions"]>0
        fname=f"reports/c84-{case}-{'observer' if enabled else 'baseline'}.stderr"
        Path(fname).write_bytes(proc.stderr)
        observations.append({
            "observer":enabled,"verdict":verdict,
            "first_c56_pair":pairs[0],"work":work,
            "exact_closure_census":c84,
            "stderr_sha256":hashlib.sha256(proc.stderr).hexdigest(),
        })
    assert observations[0]["first_c56_pair"]==observations[1]["first_c56_pair"]
    assert observations[0]["work"]==observations[1]["work"],(case,observations)
    rows.append({"case":case,"profile_expr":profile_expr,"original_sha256":expected_hash,
                 "baseline_observer_work_equal":True,"observations":observations})
    print("C84_ORIGINAL_CASE="+json.dumps({
        "case":case,
        "verdicts":[o["verdict"] for o in observations],
        "source_work_unchanged":True,
        "closure_census":observations[1]["exact_closure_census"],
    },sort_keys=True),flush=True)
result={
    "experiment":"C84 exact closure identity census inside frozen first failing root",
    "selected_C58_source_unchanged":True,
    "original_proofs_unchanged":True,
    "standard_budget":262144,
    "normal_kernel_proof_rules_changed":False,
    "new_cache_or_result_reuse":False,
    "observer_off_on_equivalence":True,
    "original_standard_accepts":0,
    "full_403_protected_corpus_not_run":True,
    "rows":rows,
}
Path("reports/c84.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
