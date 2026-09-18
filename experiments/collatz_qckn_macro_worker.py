#!/usr/bin/env python3
"""QCKN-controlled application of a verified Collatz forward-macro bank.

This worker does not learn macros. It accepts a bank emitted by QCKN, verifies
the serialized macro algebra locally, and applies the bank prospectively to a
declared source range using the exact replay logic from the pinned transfer
experiment.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

import collatz_forward_descent_macro_transfer as fm
import collatz_fragment_transfer_probe as ft


def load_bank(path:str):
    payload=json.loads(Path(path).read_text())
    if payload.get("version")!="collatz-forward-macro-bank-v1":
        raise ValueError("unsupported macro bank version")
    bank=defaultdict(list)
    ids=set()
    for row in payload.get("macros",()):
        mid=str(row["macro_id"])
        if mid in ids:
            raise ValueError("duplicate macro id")
        ids.add(mid)
        word=tuple(tuple(int(v) for v in t) for t in row["word"])
        c=ft.fragment_cert(word)
        for key in ("r0","r1","A","B","D","steps"):
            if int(c[key])!=int(row[key]):
                raise ValueError(f"macro algebra mismatch {mid} {key}")
        c["macro_id"]=mid
        bank[c["r0"]].append(c)
    return payload,{r:tuple(v) for r,v in bank.items()}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bank-json",required=True)
    ap.add_argument("--lo",type=int,required=True)
    ap.add_argument("--hi",type=int,required=True)
    ap.add_argument("--K",type=int,default=96)
    ap.add_argument("--out-json",required=True)
    a=ap.parse_args()

    payload,bank=load_bank(a.bank_json)
    cnt,closed,hard,best=fm.test(bank,a.lo,a.hi,a.K)
    result={
        "version":"collatz-qckn-macro-worker-result-v1",
        "source_range":[a.lo,a.hi],
        "K":a.K,
        "macro_bank_digest":payload["bank_digest"],
        "macro_count":payload["macro_count"],
        "counts":dict(cnt),
        "closed_sources":[int(row[1]) for row in closed],
        "hard_sources":[int(n) for n in hard],
        "first_closed":[list(row[:-1])+[[list(t) for t in row[-1]]] for row in closed[:30]],
    }
    Path(a.out_json).write_text(
        json.dumps(result,sort_keys=True,separators=(",",":"))+"\n"
    )
    print("BANK_MACROS",payload["macro_count"])
    print("BANK_DIGEST",payload["bank_digest"])
    print("HELD",a.lo,a.hi,"COUNTS",dict(cnt))
    print("CLOSED",len(closed))
    print("HARD",len(hard),"FIRST_HARD",hard[:60])
    if closed:
        print("PASS_QCKN_MACRO_REUSE")
    else:
        print("NO_QCKN_MACRO_REUSE")
    print("STATUS BOUNDED_QCKN_MACRO_WORKER")


if __name__=="__main__":
    main()
