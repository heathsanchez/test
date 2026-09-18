#!/usr/bin/env python3
"""Candidate acquisition for QCKN-controlled Collatz forward-descent macros.

Learns only from the declared training range.  Output is a candidate evidence
artifact; it is not active memory and performs no promotion.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

import collatz_forward_descent_macro_transfer as fm
import collatz_fragment_transfer_probe as ft


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"))


def macro_row(c):
    word=tuple(tuple(int(v) for v in t) for t in c["word"])
    check=ft.fragment_cert(word)
    for key in ("r0","r1","A","B","D","steps"):
        assert int(check[key])==int(c[key]),(key,check[key],c[key])
    body={
        "r0":int(c["r0"]),"r1":int(c["r1"]),
        "A":int(c["A"]),"B":int(c["B"]),"D":int(c["D"]),
        "steps":int(c["steps"]),
        "word":[list(t) for t in word],
    }
    ident="macro-"+hashlib.sha256(canonical(body).encode()).hexdigest()[:20]
    return {"macro_id":ident,**body}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train-hi",type=int,default=8191)
    ap.add_argument("--maxlen",type=int,default=12)
    ap.add_argument("--out-json",required=True)
    a=ap.parse_args()

    sources,bank,count=fm.learn(3,a.train_hi,a.maxlen)
    rows=[]
    for r in sorted(bank):
        for c in bank[r]:
            rows.append(macro_row(c))
    rows=sorted(rows,key=lambda x:x["macro_id"])
    assert len(rows)==count==len({r["macro_id"] for r in rows})

    payload={
        "version":"collatz-forward-macro-candidate-v1",
        "train_range":[3,a.train_hi],
        "training_sources":sources,
        "maxlen":a.maxlen,
        "macro_count":len(rows),
        "anchors":len(bank),
        "macros":rows,
    }
    payload["evidence_digest"]=hashlib.sha256(canonical(payload).encode()).hexdigest()
    Path(a.out_json).write_text(canonical(payload)+"\n")
    print("TRAIN",3,a.train_hi,"SOURCES",sources,"MACROS",len(rows),
          "ANCHORS",len(bank),"MAXLEN",a.maxlen)
    print("EVIDENCE_DIGEST",payload["evidence_digest"])
    print("PASS_QCKN_MACRO_CANDIDATE_ACQUISITION")


if __name__=="__main__":
    main()
