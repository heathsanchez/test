from __future__ import annotations
import json
from basis import parse_prefix_free, run_machine, Machine
from kernel import Kernel
from challenge_pack import make_world, heldout_rows, hidden_codebook_strings

def cb_from(r):
    return tuple(tuple(int(ch) for ch in w) for w in r["codebook"])

def machine_from(r):
    d=r["machine"]
    return Machine(int(d["initial"]), tuple(int(x) for x in d["outputs"]), tuple(tuple(int(z) for z in t) for t in d["transitions"]))

def exact(rows, cb, m):
    for row in rows:
        seq=parse_prefix_free(tuple(row.raw), cb)
        if seq is None or run_machine(m,seq)!=int(row.consequence):
            return False
    return True

out={}
k=Kernel()
for kind in ("relation2","relation3"):
    out[kind]={}
    for depth in range(3,9):
        out[kind][str(depth)]={}
        for flip in (0,1):
            r=k.synthesize(make_world(kind,flip=flip,max_tokens=depth))
            row={"status":r.get("status"),"state_count":r.get("state_count")}
            if r.get("status")=="VERIFIED":
                cb=cb_from(r); m=machine_from(r)
                row.update({
                    "codebook":r.get("codebook"),
                    "hidden_codebook_recovered":set(r["codebook"])==hidden_codebook_strings(kind,flip),
                    "heldout_to_8_exact":exact(heldout_rows(kind,flip=flip,max_tokens=8),cb,m),
                    "distinguishing_horizon":r.get("distinguishing_horizon"),
                    "construction_depth":r.get("construction_depth"),
                })
            out[kind][str(depth)][str(flip)]=row
print(json.dumps(out,indent=2,sort_keys=True))
