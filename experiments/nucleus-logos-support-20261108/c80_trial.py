"""C80 independent process A/B n7 cold test and false-proof controls.

Comparisons charge actual original source 262144 steps and include the new
key/lookup cost. Never claim a speed win from unequal verdicts or diagnostic
high-budget ACCEPT. Requires exact original source SHA and 24 selected flags.
"""
import hashlib,json,os,pathlib,subprocess,time,statistics
ROOT=pathlib.Path("arena207")
ORIG=ROOT.joinpath("good/perf/magma-list-pair-n7.ndjson").read_bytes()
SOURCE_SHA=hashlib.sha256(ORIG).hexdigest()
assert SOURCE_SHA=="abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
FLAGS=json.loads(pathlib.Path("base/flags.json").read_text())
assert len(FLAGS)==24 and set(FLAGS.values())=={"1"}
BIN=str(pathlib.Path("candidate/nucleus-diagnostic").resolve())
OUT=pathlib.Path("reports")
OUT.mkdir(exist_ok=True)
VERDICTS={0:"ACCEPT",1:"REJECT",2:"UNKNOWN",3:"ERROR"}
cases=[
    ("n7", "good/perf/magma-list-pair-n7.ndjson", "valid"),
    ("nat-rec", "bad/bugs/nat-rec-rules.ndjson", "invalid"),
    ("orphan-rec","bad/bugs/orphan-rec.ndjson","invalid"),
]
allrows=[]
for budget,trial_count in [(262144,3),(8388608,1)]:
  for label,path,cls in cases:
    if budget!=262144 and cls!="valid":continue
    source=ROOT.joinpath(path).read_bytes()
    for mode in ("A_off","B_completed_numeral_share"):
      for trial in range(trial_count if cls=="valid" else 1):
        env={k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(FLAGS)
        env.update({
            "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
            "NUCLEUS_EXPERIMENTAL_RESUMABLE_EXPOSURE":"1",
        })
        if mode=="B_completed_numeral_share":
            env["NUCLEUS_C80_EXACT_NAT_VALUE_SHARE"]="1"
            env["NUCLEUS_C80_ARITH_TRACE"]="1"
        start=time.monotonic()
        proc=subprocess.run([BIN,str(budget)],input=source,capture_output=True,env=env,timeout=180)
        seconds=time.monotonic()-start
        verdict=VERDICTS.get(proc.returncode,"ERROR")
        if cls=="valid":assert verdict in ("UNKNOWN","ACCEPT"),("false reject/error",label,mode,verdict)
        else:assert verdict in ("REJECT","UNKNOWN"),("INVALID ACCEPT",label,mode,verdict)
        lines=proc.stderr.decode(errors="replace").splitlines()
        events=[z for z in lines if z.startswith("NUCLEUS_C80_ARITH:")]
        record=dict(budget=budget,case=label,kind=cls,mode=mode,trial=trial,
                    verdict=verdict,wall_seconds=round(seconds,5),
                    source_sha256=hashlib.sha256(source).hexdigest(),
                    hash_bytes=proc.stderr and hashlib.sha256(proc.stderr).hexdigest(),
                    cache_event_samples=events)
        allrows.append(record)
        if trial==0 or verdict=="ACCEPT":
            print("C80_ARM="+json.dumps({k:v for k,v in record.items() if k!="cache_event_samples"},sort_keys=True),
                  "cache_samples="+str(events[-5:]),flush=True)
        (OUT/f"c80-{budget}-{label}-{mode}-{trial}.stderr").write_bytes(proc.stderr)
def summary(budget,label,mode):
    rows=[r for r in allrows if (r["budget"],r["case"],r["mode"])==(budget,label,mode)]
    return {"verdicts":[r["verdict"] for r in rows],
            "median_wall_seconds":round(statistics.median(r["wall_seconds"] for r in rows),5),
            "cache_witnesses":sum(len(r["cache_event_samples"]) for r in rows)}
a=summary(262144,"n7","A_off")
b=summary(262144,"n7","B_completed_numeral_share")
assert a["verdicts"]==["UNKNOWN"]*3,"same-source baseline drift"
new_accepts=sum(v=="ACCEPT" for v in b["verdicts"])
s={
 "experiment":"C80 owner-qualified completed NativeNat arithmetic cross-environment memoization",
 "source_sha256":SOURCE_SHA,
 "all_original_inputs_unchanged":True,
 "selected_checker_changed":False,
 "proof_rules_changed":False,
 "standard_budget":262144,
 "standard_new_accept_replays":new_accepts,
 "original_n7_A":a,"original_n7_B":b,
 "high_A":summary(8388608,"n7","A_off"),
 "high_B":summary(8388608,"n7","B_completed_numeral_share"),
 "full_protected_403_not_run":True,
 "all_native_tests_pending":True,
 "rows":allrows,
}
(OUT/"c80.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
print("C80_RESULT="+json.dumps({k:v for k,v in s.items() if k in ("standard_new_accept_replays","original_n7_A","original_n7_B","high_A","high_B")},sort_keys=True),flush=True)
