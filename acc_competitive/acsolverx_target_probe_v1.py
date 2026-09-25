#!/usr/bin/env python3
"""Narrow ACSolverX trajectory-source probe for current ACC targets.

Scientific boundary:
- target states come from the pinned official verifier manifest;
- ACSolverX data/model are bound to one exact public commit;
- dataset membership and S-move beam paths are candidate trajectory sources only;
- no candidate is an ACC certificate until compiled to ac-r2-v1 and replayed by
  the pinned official verifier.
"""
import argparse, ast, gzip, hashlib, json, sqlite3
from pathlib import Path

TARGETS=("ac-10090","ac-06708")

def inv(w):
    return tuple(-x for x in reversed(w))

def rotations(w):
    if not w:
        return [()]
    return [w[i:]+w[:i] for i in range(len(w))]

def canon_word(w):
    w=tuple(w)
    return min(rotations(w)+rotations(inv(w)))

def canon_pair(s):
    a,b=canon_word(tuple(s[0])),canon_word(tuple(s[1]))
    return tuple(sorted((a,b)))

def flat(s,L=24):
    a,b=tuple(s[0]),tuple(s[1])
    if len(a)>L or len(b)>L:
        raise ValueError((len(a),len(b),L))
    return list(a)+[0]*(L-len(a))+list(b)+[0]*(L-len(b))

def line_key(v):
    return tuple(int(x) for x in v)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--ac1m",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    m=json.loads(Path(a.manifest).read_text())
    byid={c["challenge_id"]:c for c in m["challenges"]}
    exact={}
    canon={}
    meta={}
    for cid in TARGETS:
        c=byid[cid]
        s=tuple(tuple(int(x) for x in w) for w in c["initial_relators"])
        cs=canon_pair(s)
        exact[cid]=line_key(flat(s))
        canon[cid]=line_key(flat(cs))
        meta[cid]={
            "relator_lengths":[len(s[0]),len(s[1])],
            "total_length":len(s[0])+len(s[1]),
            "exact_flat_sha256":hashlib.sha256(json.dumps(exact[cid],separators=(",",":")).encode()).hexdigest(),
            "canonical_flat_sha256":hashlib.sha256(json.dumps(canon[cid],separators=(",",":")).encode()).hexdigest(),
            "canonical_changed":exact[cid]!=canon[cid],
        }
    (out/"targets_exact.txt").write_text("".join(repr(list(exact[c]))+"\n" for c in TARGETS))
    (out/"targets_canonical.txt").write_text("".join(repr(list(canon[c]))+"\n" for c in TARGETS))
    (out/"target_ids.json").write_text(json.dumps(list(TARGETS),indent=2)+"\n")

    exact_hits={c:[] for c in TARGETS}
    canon_hits={c:[] for c in TARGETS}
    n=0
    with gzip.open(a.ac1m,"rt") as f:
        for n,line in enumerate(f,1):
            try:
                v=line_key(ast.literal_eval(line.strip()))
            except Exception as e:
                raise RuntimeError(f"bad AC1M line {n}: {e}")
            for cid in TARGETS:
                if v==exact[cid]: exact_hits[cid].append(n-1)
                if v==canon[cid]: canon_hits[cid].append(n-1)
    rep={
        "schema":"acc-acsolverx-target-probe-v1",
        "targets":meta,
        "ac1m_rows":n,
        "exact_membership":exact_hits,
        "canonical_membership":canon_hits,
        "membership_hits":sum(len(v) for v in exact_hits.values())+sum(len(v) for v in canon_hits.values()),
        "claim_boundary":"Membership is only a trajectory-source diagnostic. ACSolverX S-moves are not official ACC certificates.",
    }
    (out/"membership.json").write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n")
    print("ACSOLVERX_MEMBERSHIP",json.dumps(rep,sort_keys=True))

if __name__=="__main__":
    main()
