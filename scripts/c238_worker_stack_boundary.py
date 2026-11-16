"""C238: bounded worker-stack audit of unchanged original app-lam and controls.

No semantic rule or global inference budget changes. A crash is an explicit
negative signal, never a proof-quality verdict. The default 64MiB is retained.
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
CONTROLS = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)
EXTRAS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)

def replay(checker, source, env, path, label, timeout):
    start = time.monotonic()
    try:
        r = subprocess.run([str(checker)], input=source, env=env,
                           capture_output=True, timeout=timeout, check=False)
        stderr = r.stderr.decode(errors="replace")
        code = r.returncode
    except subprocess.TimeoutExpired as e:
        stderr = (e.stderr or b"").decode(errors="replace")
        code = None
    (path / (label + ".stderr")).write_text(stderr)
    return {"label": label, "exit": code,
            "time_s": round(time.monotonic()-start, 2),
            "overflow": "has overflowed its stack" in stderr,
            "source_sha256": hashlib.sha256(source).hexdigest()}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--checker", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if hashlib.sha256(a.archive.read_bytes()).hexdigest() != ARCHIVE:
        raise ValueError("Original archive SHA-256 mismatch")
    flags = json.loads(a.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Historical flags changed")
    env = {k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    with zipfile.ZipFile(a.archive) as z:
        original = {r["case"]: r for r in json.loads(z.read("current212.json"))}
        if len(original) != 212: raise ValueError("Corpus changed")
        def source(case):
            value = z.read("inputs/" + case)
            if hashlib.sha256(value).hexdigest() != original[case]["sha256"]:
                raise ValueError("Source altered: " + case)
            return value
        app = source("good/perf/app-lam.ndjson")
        if hashlib.sha256(app).hexdigest() != APP_LAM or original["good/perf/app-lam.ndjson"]["expected"] != 0:
            raise ValueError("Wrong app-lam source")
        rows = []
        for stack in (64, 128, 256):
            e=env.copy()
            e["NUCLEUS_C238_STACK_MIB"] = str(stack)
            r=replay(a.checker, app, e, a.out, "app-lam-stack"+str(stack), timeout=90)
            r["stack_mib"] = stack
            if r["exit"] == 1: raise ValueError("Incorrect REJECT of valid source: "+str(r))
            if r["exit"] not in (0, 2, -6, None): raise ValueError("Unexpected failure: "+str(r))
            print("C238_STACK", json.dumps(r, sort_keys=True), flush=True)
            rows.append(r)
        if rows[0]["exit"] != -6 or not rows[0]["overflow"]:
            raise ValueError("Default 64MiB stack overflow not reproduced")
        controls=[]
        for case in CONTROLS:
            e=env.copy()
            e["NUCLEUS_C238_STACK_MIB"] = "256"
            r=replay(a.checker, source(case), e, a.out,
                     "control_"+case.replace("/","_").removesuffix(".ndjson"),timeout=60)
            r["original"]=case
            if r["exit"] != original[case]["expected"] or r["exit"] not in (0,1):
                raise ValueError("Protected control verdict changed: "+str(r))
            controls.append(r)
    report={"state":"WARRANTED_BOUNDED_IF_CI_GREEN",
            "source_archive":ARCHIVE, "app_lam_sha256":APP_LAM,
            "stack_sweep":rows, "protected_controls":controls,
            "no_semantic_rule_change":True,
            "app_lam_accept_on_expanded_stack":any(r["exit"]==0 for r in rows[1:])}
    (a.out/"c238-report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("C238_SUMMARY",json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
