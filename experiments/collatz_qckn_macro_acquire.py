#!/usr/bin/env python3
"""Candidate acquisition for QCKN-controlled Collatz forward-descent macros.

Learns only from the declared training range.  Output is a candidate evidence
artifact; it is not active memory and performs no promotion.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
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


def learn_sources(sources,maxlen):
    bank=defaultdict(dict)
    used=0
    for n in sorted(set(int(x) for x in sources)):
        if not fm.candidate(n):
            continue
        starts,words=fm.q0_odd_starts_and_words(n)
        if not words:
            continue
        used+=1
        end=len(words)
        for a in range(max(0,end-maxlen),end):
            w=tuple(words[a:end])
            try:
                cert=ft.fragment_cert(w)
            except AssertionError:
                continue
            key=(cert["r0"],cert["r1"],cert["A"],cert["B"],cert["D"],cert["word"])
            bank[cert["r0"]].setdefault(key,cert)
    out={r:list(d.values()) for r,d in bank.items()}
    return used,out,sum(len(v) for v in out.values())


def load_excluded_ids(path):
    if not path:
        return set()
    payload=json.loads(Path(path).read_text())
    if payload.get("version")!="collatz-forward-macro-bank-v1":
        raise ValueError("unsupported exclude macro bank")
    return {str(row["macro_id"]) for row in payload.get("macros",())}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train-hi",type=int,default=8191)
    ap.add_argument("--maxlen",type=int,default=12)
    ap.add_argument("--sources-json")
    ap.add_argument("--source-key",default="hard_sources")
    ap.add_argument("--exclude-bank-json")
    ap.add_argument("--out-json",required=True)
    a=ap.parse_args()

    explicit=None
    if a.sources_json:
        source_payload=json.loads(Path(a.sources_json).read_text())
        explicit=[int(x) for x in source_payload[a.source_key]]
        sources,bank,count=learn_sources(explicit,a.maxlen)
        train_range=None
        mode="explicit_sources"
    else:
        sources,bank,count=fm.learn(3,a.train_hi,a.maxlen)
        train_range=[3,a.train_hi]
        mode="contiguous_range"

    rows=[]
    for r in sorted(bank):
        for c in bank[r]:
            rows.append(macro_row(c))
    rows=sorted(rows,key=lambda x:x["macro_id"])
    assert len(rows)==count==len({r["macro_id"] for r in rows})
    raw_count=len(rows)
    excluded=load_excluded_ids(a.exclude_bank_json)
    if excluded:
        rows=[row for row in rows if row["macro_id"] not in excluded]
    anchors=len({row["r0"] for row in rows})

    payload={
        "version":"collatz-forward-macro-candidate-v1",
        "training_mode":mode,
        "train_range":train_range,
        "training_sources":sources,
        "training_sources_requested":len(explicit) if explicit is not None else None,
        "training_source_digest":(
            hashlib.sha256(canonical(sorted(explicit)).encode()).hexdigest()
            if explicit is not None else ""
        ),
        "maxlen":a.maxlen,
        "raw_macro_count":raw_count,
        "excluded_macro_count":raw_count-len(rows),
        "macro_count":len(rows),
        "anchors":anchors,
        "macros":rows,
    }
    payload["evidence_digest"]=hashlib.sha256(canonical(payload).encode()).hexdigest()
    Path(a.out_json).write_text(canonical(payload)+"\n")
    if explicit is None:
        print("TRAIN",3,a.train_hi,"SOURCES",sources,"MACROS",len(rows),
              "ANCHORS",anchors,"MAXLEN",a.maxlen)
    else:
        print("TRAIN_EXPLICIT","REQUESTED",len(explicit),"USED",sources,
              "RAW_MACROS",raw_count,"NEW_MACROS",len(rows),
              "EXCLUDED",raw_count-len(rows),"ANCHORS",anchors,
              "MAXLEN",a.maxlen)
    print("EVIDENCE_DIGEST",payload["evidence_digest"])
    print("PASS_QCKN_MACRO_CANDIDATE_ACQUISITION")


if __name__=="__main__":
    main()
