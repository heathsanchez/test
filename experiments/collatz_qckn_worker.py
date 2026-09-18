#!/usr/bin/env python3
"""QCKN-controlled Collatz C9 worker.

This worker contains no active endpoint memory of its own.  A verified endpoint
bank is supplied by the QCKN CompiledPresent as JSON.

For each source in the assigned range:
  * require hereditary q=0 RIGID birth;
  * stop immediately on ordinary direct descent;
  * detect the exact C9 two-replay endpoint cylinder;
  * require the hit and both C9 replays to remain RIGID;
  * reuse a supplied endpoint capability when available;
  * otherwise independently verify the concrete endpoint tail to 1 once and
    emit a candidate acquisition.

The worker never promotes anything.  Promotion belongs to QCKN authority.

Bounded discovery only; not a proof of Collatz.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import collatz_q0_coalescence_component_audit as base
import collatz_q0_rigid_recharge_audit as ra

XRES=468713
XMOD=1<<20
WORD=((1,1,4),(4,1,1),(1,1,1))
CERT=ra.certificate(WORD)
L=sum(r+s for r,s,rp in WORD)


def canonical_json(obj)->str:
    return json.dumps(obj,sort_keys=True,separators=(",",":"))


def bank_digest(bank:dict[int,int])->str:
    rows=sorted((int(k),int(v)) for k,v in bank.items())
    return hashlib.sha256(canonical_json(rows).encode()).hexdigest()


def endpoint_certificate(x:int,guard:int)->int|None:
    y=x
    for t in range(guard+1):
        if y==1:
            return t
        y=base.T(y)
    return None


def load_bank(path:str,guard:int)->dict[int,int]:
    payload=json.loads(Path(path).read_text())
    if payload.get("version")!="collatz-endpoint-bank-v1":
        raise ValueError("unsupported endpoint bank version")
    rows=payload.get("endpoints",{})
    bank={int(k):int(v) for k,v in rows.items()}
    for x,steps in sorted(bank.items()):
        actual=endpoint_certificate(x,guard)
        if actual!=steps:
            raise ValueError(f"bank verification failed for {x}: {actual} != {steps}")
    return bank


def rigid_prefix(n:int,k0:int,k1:int):
    for k in range(k0,k1+1):
        out,data=base.cylinder_status(k,n)
        if out!="RIGID":
            return False,(k,out,data)
    return True,None


def replay_twice(n:int,k:int,y:int):
    m=(y+1)//2
    m1=ra.replay(CERT,m)
    m2=ra.replay(CERT,m1)
    z=y
    kk=k
    first_non=None
    for rep,target in enumerate((m1,m2),1):
        for _ in range(L):
            z=base.T(z)
            kk+=1
            if first_non is None:
                out,data=base.cylinder_status(kk,n)
                if out!="RIGID":
                    first_non=(rep,kk,out,data,z)
        assert z==2*target-1
    return first_non is None,(m,m1,m2,z,kk,first_non)


def audit(lo:int,hi:int,H:int,guard:int,bank:dict[int,int]):
    counts=Counter()
    reuse=Counter()
    candidates={}
    unresolved=[]

    for n in range(max(3,lo)|1,hi+1,2):
        if base.birth_status(n)[0]!="RIGID":
            continue
        ok,_=base.survives_to_q0(n)
        if not ok:
            continue
        counts["hereditary_birth_rigid"]+=1

        k0=n.bit_length()
        _,y=base.forward_state(k0,n)
        for t in range(H+1):
            if t:
                y=base.T(y)

            if y<n:
                counts["post_q0_direct_descent"]+=1
                break

            if y%XMOD!=XRES:
                continue

            counts["raw_high_fuel_hit"]+=1
            k=k0+t
            live,_why=rigid_prefix(n,k0,k)
            if not live:
                counts["hit_after_rigid_exit"]+=1
                continue

            counts["live_high_fuel_hit"]+=1
            all_rigid,trace=replay_twice(n,k,y)
            if not all_rigid:
                counts["replay_breaker"]+=1
                continue

            counts["live_two_replay"]+=1

            if y in bank:
                reuse[y]+=1
                counts["compiled_reuse_hit"]+=1
                counts["closed_hit"]+=1
                continue

            steps=endpoint_certificate(y,guard)
            if steps is None:
                row={
                    "source":n,
                    "k":k,
                    "endpoint":y,
                    "trace":repr(trace),
                }
                unresolved.append(row)
                counts["unresolved_hit"]+=1
                continue

            counts["verified_candidate_hit"]+=1
            counts["closed_hit"]+=1
            row=candidates.get(y)
            if row is None:
                candidates[y]={
                    "endpoint":y,
                    "steps_to_one":steps,
                    "first_source":n,
                    "first_k":k,
                    "occurrences":1,
                }
                counts["candidate_verifier_calls"]+=1
            else:
                assert row["steps_to_one"]==steps
                row["occurrences"]+=1
                counts["candidate_duplicate_reuse"]+=1

    return {
        "version":"collatz-qckn-worker-result-v1",
        "source_range":[lo,hi],
        "horizon":H,
        "guard":guard,
        "bank_digest":bank_digest(bank),
        "bank_size":len(bank),
        "counts":dict(sorted(counts.items())),
        "reuse":{str(k):v for k,v in sorted(reuse.items())},
        "candidate_acquisitions":[candidates[k] for k in sorted(candidates)],
        "unresolved":unresolved,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lo",type=int,required=True)
    ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--H",type=int,default=512)
    ap.add_argument("--guard",type=int,default=10000)
    ap.add_argument("--bank-json",required=True)
    ap.add_argument("--out-json",required=True)
    a=ap.parse_args()

    bank=load_bank(a.bank_json,a.guard)
    result=audit(a.lo,a.hi,a.H,a.guard,bank)
    Path(a.out_json).write_text(canonical_json(result)+"\n")

    print("SOURCE_RANGE",a.lo,a.hi)
    print("BANK_SIZE",result["bank_size"])
    print("BANK_DIGEST",result["bank_digest"])
    print("COUNTS",result["counts"])
    print("CANDIDATE_ACQUISITIONS",len(result["candidate_acquisitions"]))
    for row in result["candidate_acquisitions"]:
        print("CANDIDATE",row)
    print("UNRESOLVED",len(result["unresolved"]))
    if result["unresolved"]:
        print("SEPARATOR_QCKN_WORKER_UNRESOLVED",result["unresolved"][0])
    else:
        print("PASS_QCKN_WORKER_NO_UNRESOLVED")
    print("STATUS BOUNDED_QCKN_CONTROLLED_WORKER")


if __name__=="__main__":
    main()
