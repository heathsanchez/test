"""C239: source-pinned, no-wrong complete current212 qualification at 128MiB.

The 128MiB choice is a resource change only, with no altered kernel
judgment or new equality authority. Old 122 ACCEPT / 84 REJECT / 6 UNKNOWN
source-verdict vector is checked case by case, not treated as a soundness
certificate for every future source.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

ARCHIVE = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
APP_LAM = "552d6e8398f579fcf59ab9abd8187fc7a8a037697da66c129aacb4cc1b9dd414"
EXTRAS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)

def run(checker: Path, content: bytes, env: dict, timeout: int = 240):
    started = time.monotonic()
    try:
        proc = subprocess.run([str(checker)], input=content, env=env,
                              capture_output=True, timeout=timeout, check=False)
        return proc.returncode, proc.stderr.decode(errors="replace"), round(time.monotonic()-started, 3)
    except subprocess.TimeoutExpired as exc:
        return None, (exc.stderr or b"").decode(errors="replace"), round(time.monotonic()-started, 3)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--checker", type=Path, required=True)
    p.add_argument("--flags", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE:
        raise ValueError("Original artifact changed")
    flags = json.loads(args.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Historical 24 flags changed")
    env = {k: v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}": "1" for k in EXTRAS})
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    # Default worker stack must be exercised without explicit C238 override.
    if "NUCLEUS_C238_STACK_MIB" in env:
        raise ValueError("Explicit worker-stack override is forbidden")

    rows = []
    with zipfile.ZipFile(args.archive) as z:
        old = {r["case"]:r for r in json.loads(z.read("current212.json"))}
        if len(old)!=212:
            raise ValueError("Wrong source corpus")
        baseline = {k:sum(r["actual"] == k for r in old.values()) for k in (0,1,2)}
        if baseline != {0:122, 1:84, 2:6}:
            raise ValueError("Expected corpus baseline changed: "+str(baseline))
        for case in sorted(old):
            b=z.read("inputs/"+case)
            h=hashlib.sha256(b).hexdigest()
            if h!=old[case]["sha256"]:
                raise ValueError("Source hash drift: "+case)
            code,log,elapsed=run(args.checker,b,env)
            row={"case":case,"sha256":h,"expected":old[case]["expected"],
                 "historical":old[case]["actual"],"observed":code,
                 "time_s":elapsed,
                 "terminal": [x for x in log.splitlines()
                              if x.startswith("NUCLEUS_DOWNSTREAM:")][-1:]}
            if code not in (0,1,2):
                row["failure_tail"]=log[-300:]
            rows.append(row)
            if (code==0 and old[case]["expected"]!=0) or (
                    code==1 and old[case]["expected"]!=1):
                raise ValueError("Incorrect decisive verdict: "+str(row))
            # A historical decisive result must not regress. UNKNOWN inputs
            # may become ACCEPT only if genuinely valid (corpus expected=0).
            if old[case]["actual"] in (0,1) and code!=old[case]["actual"]:
                raise ValueError("Historical decisive verdict regression: "+str(row))
            if old[case]["actual"]==2 and code not in (0,2):
                raise ValueError("Original UNKNOWN became invalid/crash: "+str(row))
            if case=="good/perf/app-lam.ndjson" and (
                code!=0 or h!=APP_LAM):
                raise ValueError("Original 20k-deep app-lam must ACCEPT: "+str(row))
            print("C239_CASE",json.dumps(row,sort_keys=True),flush=True)
    assert len(rows)==212
    counts={str(k):sum(r["observed"]==k for r in rows) for k in (0,1,2)}
    summary={"status":"WARRANTED_BOUNDED_IF_GITHUB_SUCCESS",
             "head_scope":"current212 original Lean4.34.1 NDJSON3.1",
             "source_archive_sha256":ARCHIVE,
             "selected_default_stack_mib":128,
             "no_wrong_or_crash":True,
             "histogram":counts,
             "new_accepts":[r["case"] for r in rows if r["historical"]==2 and r["observed"]==0],
             "remaining_unknowns":[r["case"] for r in rows if r["observed"]==2],
             "app_lam_recovered":True,"rows":rows}
    (args.out/"c239-current212.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print("C239_SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="rows"},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
