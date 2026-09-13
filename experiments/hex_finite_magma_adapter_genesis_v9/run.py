#!/usr/bin/env python3
import itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
V8=ROOT.parent/"hex_meta_language_substrate_genesis_v8"/"AUTHORITY.json"
NAMES=("T_L","T_R","T_O","A_L","A_R","A_O")

def load_v8():
    x=json.loads(V8.read_text())
    if x.get("verdict")!="VERIFIED_META_LANGUAGE_PRIMITIVE_GENESIS_AND_TRANSFER":
        raise RuntimeError("V8 authority missing")
    return x

def magmas2():
    return [tuple((bits>>i)&1 for i in range(4)) for bits in range(16)]

def relabel(table,n,p):
    out=[0]*(n*n)
    for x in range(n):
        for y in range(n):
            z=table[x*n+y]
            out[p[x]*n+p[y]]=p[z]
    return tuple(out)

def source_canon(table,n):
    return min(relabel(table,n,p) for p in itertools.permutations(range(n)))

def target_canon(table,n,mask):
    tl,tr,to,al,ar,ao=[bool(mask&(1<<k)) for k in range(6)]
    perms=list(itertools.permutations(range(n)))
    best=None
    for pL,pR,pO,pA in itertools.product(perms,repeat=4):
        tuples=[]
        for x in range(n):
            for y in range(n):
                z=table[x*n+y]
                sig=[]
                if tl: sig.append((0,pL[x]))
                if tr: sig.append((1,pR[y]))
                if to: sig.append((2,pO[z]))
                tuples.append(tuple(sig))
        tuples=tuple(sorted(tuples))
        anchors=[]
        if al: anchors.append((3,0,tuple(sorted((pA[v],pL[v]) for v in range(n)))))
        if ar: anchors.append((3,1,tuple(sorted((pA[v],pR[v]) for v in range(n)))))
        if ao: anchors.append((3,2,tuple(sorted((pA[v],pO[v]) for v in range(n)))))
        sig=(tuples,tuple(anchors))
        if best is None or sig<best: best=sig
    return best

def evaluate(mask,tables,src):
    ts=[target_canon(t,2,mask) for t in tables]
    mm=0
    first=None
    for i in range(len(tables)):
        for j in range(len(tables)):
            s=src[i]==src[j]
            u=ts[i]==ts[j]
            if s!=u:
                mm+=1
                if first is None:
                    first={"a":list(tables[i]),"b":list(tables[j]),
                           "source_iso":s,"target_iso":u}
    return {
      "mask":mask,
      "channels":[NAMES[k] for k in range(6) if mask&(1<<k)],
      "channel_count":mask.bit_count(),
      "mismatch_count":mm,
      "qualified":mm==0,
      "first_mismatch":first,
    }

def main():
    v8=load_v8()
    tables=magmas2()
    src=[source_canon(t,2) for t in tables]

    cold=[evaluate(mask,tables,src) for mask in range(64)]
    cq=[x for x in cold if x["qualified"]]

    anchor_mask=(1<<3)|(1<<4)|(1<<5)
    warm_masks=[anchor_mask|m for m in range(8)]
    warm=[evaluate(mask,tables,src) for mask in warm_masks]
    wq=[x for x in warm if x["qualified"]]

    winner=cq[0] if len(cq)==1 else None
    ablations=[]
    if winner:
        for k,name in enumerate(NAMES):
            m=winner["mask"] & ~(1<<k)
            ev=evaluate(m,tables,src)
            ablations.append({"removed":name,"mismatch_count":ev["mismatch_count"],
                              "first_mismatch":ev["first_mismatch"]})

    gates={
      "G1_complete_source_world":len(tables)==16,
      "G2_cold_count_64":len(cold)==64,
      "G3_unique_cold_winner":len(cq)==1,
      "G4_cold_winner_all_six":bool(winner and winner["mask"]==63),
      "G5_warm_count_8":len(warm)==8,
      "G6_unique_warm_winner":len(wq)==1,
      "G7_warm_winner_all_tuple_channels":bool(wq and wq[0]["mask"]==63),
      "G8_same_winner":bool(winner and wq and winner["mask"]==wq[0]["mask"]),
      "G9_all_single_channel_ablations_fail":len(ablations)==6 and all(x["mismatch_count"]>0 for x in ablations),
      "G10_prior_identity_star_available":v8["synthesized_primitive"]["bits"]=="1111",
    }

    verdict="QUALIFIED_FINITE_MAGMA_ADAPTER_FOR_HEX_HELDOUT" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence={
      "verdict":verdict,
      "classification":"FINITE_EXHAUSTIVE_MAGMA_ADAPTER_GENESIS",
      "source":{"order":2,"magmas":16,"ordered_pairs":256},
      "channel_order":list(NAMES),
      "cold":{"candidate_count":64,"qualified":cq,"ledger":cold,
              "pair_comparisons":64*256},
      "warm":{"candidate_count":8,"qualified":wq,"ledger":warm,
              "pair_comparisons":8*256},
      "reduction":8.0,
      "ablations":ablations,
      "prior_v8_run":v8["workflow_run_id"],
      "gates":gates,
      "claim_boundary":["tuple-incidence grammar supplied","order-2 exhaustive qualification","held-out order-3 only"]
    }
    OUT.mkdir(exist_ok=True)
    (OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    if winner:
        (OUT/"selected_adapter.json").write_text(json.dumps({
          "mask":winner["mask"],"channels":winner["channels"]
        },indent=2,sort_keys=True)+"\n")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
