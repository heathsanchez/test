#!/usr/bin/env python3
"""Run frozen source-specified P-256 V2 finite search and validate all counts.

Independent integer arithmetic spot-checks, source-date provenance and never-overclaim
UNKNOWN classifications are part of the program's output contract.
"""
import argparse
import ctypes
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

MOD=(1 << 107)-1
MULT=pow(3,121,MOD)
P=0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
GX=0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
LCGA=0x5DEECE66D
LCGC=0xB
SEED_TIME=871696354
MODES=["controls","f30_small","f30_time","f30_default","f62_small","f62_default","l31","chain30"]
EXPECTED={
  "f30_small":(65536,65536*192,65536*1098),
  "f30_time":(172801,172801*192,172801*1098),
  "f30_default":(1,192,1098),
  "f62_small":(65536,65536*192,65536*1122),
  "f62_default":(1,192,1122),
  "l31":(1,40000,239952),
  "chain30":(40000,40000*64,40000*55),
}

def py_limb(seed,bits,draws):
    state=seed % MOD
    bound=MOD-MOD % (1<<bits)
    out=[]
    rejects=0
    while len(out)<draws:
        state=state*MULT % MOD
        if state>=bound:
            rejects+=1
            continue
        out.append(state % (1<<bits))
    return out,rejects

def py_lrand(seed,n):
    state=((seed&0xffffffff)<<16)|0x330e
    out=[]
    for _ in range(n):
        state=(state*LCGA+LCGC)&((1<<48)-1)
        out.append(state>>17)
    return out

def independent_baselines():
    """Compare reference Python exact arithmetic and glibc lrand48 output."""
    details=[]
    for nbits in (26,30,62):
        for seed in (20420,20000,SEED_TIME,0,7157891):
            limbs,rej=py_limb(seed,nbits,25)
            assert all(0<=v<1<<nbits for v in limbs)
            state=seed%MOD
            state=state*MULT%MOD
            assert limbs[0] == state % (1<<nbits)  # no rejection for this fixed sample
            details.append({"seed":seed,"bits":nbits,"draws":25,"first3":limbs[:3],"rejections":rej})
    outputs=py_lrand(SEED_TIME,8)
    libc=ctypes.CDLL(None)
    if hasattr(libc,"srand48") and hasattr(libc,"lrand48"):
        libc.srand48.argtypes=[ctypes.c_long]
        libc.lrand48.restype=ctypes.c_long
        libc.srand48(SEED_TIME)
        actual=[libc.lrand48() for _ in range(8)]
        assert actual==outputs,(actual,outputs)
        system_lrand48="eight_outputs_equal"
    else:
        system_lrand48="not_available"
    return {"python_freeLIP_spot_checks":details,"lcg_first8":outputs,"libc_lrand48":system_lrand48}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="V2_RESULTS.json")
    ap.add_argument("--binary",default="./p256_v2_source_scan")
    ap.add_argument("--skip-running",action="store_true",help="Load existing mode JSON files, validate and consolidate")
    args=ap.parse_args()
    cwd=Path(__file__).resolve().parent
    source=cwd/"p256_v2_source_scan.cpp"
    binary=Path(args.binary).resolve()
    if not args.skip_running:
        subprocess.run(["g++","-std=c++17","-O3","-Wall","-Wextra","-o",str(binary),str(source)],check=True)
    controls=independent_baselines()
    rows=[]
    for mode in MODES:
        if args.skip_running:
            rec=json.loads((cwd/(mode+".json")).read_text())
        else:
            t0=time.monotonic()
            out=subprocess.check_output([str(binary),mode],text=True)
            rec=json.loads(out)
            (cwd/(mode+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
            print(mode, rec["exact_candidate_windows"],"hits",len(rec["hits"]),"time_s",round(time.monotonic()-t0,2),flush=True)
        assert rec["mode"]==mode and rec["status"]=="SUCCESS"
        if mode=="controls":
            assert len(rec["hits"])==3
            assert "prime239v1" in rec["hits"][0] and "offset=29" in rec["hits"][0]
            assert "synthetic_FreeLIP_30" in rec["hits"][1] and "offset=7" in rec["hits"][1]
            assert "synthetic_lrand48_31" in rec["hits"][2] and "offset=15" in rec["hits"][2]
        else:
            observed=(rec["seeds"],rec["prng_outputs"],rec["exact_candidate_windows"])
            assert observed == EXPECTED[mode],(mode,observed,EXPECTED[mode])
            assert rec["rejected_raw_steps"]==0, "If sampling rejects, check source native behavior; don't silently assume zero"
        rows.append(rec)
    searches=[x for x in rows if x["mode"]!="controls"]
    candidates=sum(r["exact_candidate_windows"] for r in searches)
    hits=[dict(mode=r["mode"],hit=h) for r in searches for h in r["hits"]]
    result={
        "scope":"FreeLIP v1.1 (1997) NBITS=30/62 native/exploratory windows, direct lrand48 top31, and companion lrand48->FreeLIP seed chaining, frozen before V2 code",
        "target":"NIST P-256 standardized base-point x-coordinate",
        "target_x_hex":hex(GX),
        "source_refs":{
            "anthropic":"https://www.anthropic.com/research/ecdsa-curve-origins",
            "FreeLIP_1997_mirror_commit":"00898a4814d2cc1244bf348682be6ed10dda35f0",
            "FreeLIP_lip_c_git_blob":"a86ce8ae5be49e0f35999a2c87f52e1718ebdb81",
            "FreeLIP_lip_h_git_blob":"080cda8aec8c0939348452ea3beb9f1afad845ef",
            "frozen_protocol":"V2_SOURCE_FROZEN_PROTOCOL.md",
        },
        "code_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "runner_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "control_results":rows[0],"independent_python_spot_checks":controls,
        "searches":searches,
        "total_exact_candidate_windows":candidates,
        "matches":hits,
        "status":"CANDIDATE_NUMERICAL_EXPLANATION_UNVALIDATED" if hits else "WARRANTED_BOUNDED_NEGATIVE_LOCAL; GENERAL_HISTORICAL_ORIGIN_UNKNOWN",
        "warrant_scope":"Exact candidate search in frozen finite grammars, not complete 1997 software or provenance; no target point G was found if matches=[]",
        "strong_comparator":"NOT_RUN (equal-information exhaustive enumerator is the only search arm)",
        "other_curves":"P-224/P-384/P-521 held untouched pending a source-derived P-256 method",
        "security":"No private-key attack, ECDSA break, or vulnerability claim",
        "next":"Locate a historically authenticated alternative PRNG or point-derivation procedure, or independently recovered generator source/link; don't widen negative grammar without decisive evidence",
    }
    path=(cwd/args.out)
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"windows":candidates,"matches":hits,"control_count":len(rows[0]["hits"]),"output":str(path)},indent=2))

if __name__=="__main__":main()
