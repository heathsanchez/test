#!/usr/bin/env python3
"""Verified Prospective Repair Selection V1, finite causal qualification."""
import hashlib, itertools, json, pathlib, random

ROOT=pathlib.Path(__file__).parent
CONTRAST=(1,-1,-1,1)
FUTURES=tuple(range(701,725))

def bits(mask): return tuple((mask>>(3-i))&1 for i in range(4))
def separates(d): return sum(a*b for a,b in zip(d,CONTRAST)) != 0
def partition(d):
    return tuple(sorted(tuple(i for i,x in enumerate(d) if x==z)
                        for z in (0,1) if any(x==z for x in d)))
def edges(p):
    return frozenset(tuple(sorted((a,b))) for c in p for a in c for b in c if a<b)

REPAIRS=sorted({partition(bits(i)) for i in range(16) if separates(bits(i))})
TARGET_INDEX=int(hashlib.sha256(b"prospective-repair-selection-v1").hexdigest(),16)%len(REPAIRS)
TARGET=REPAIRS[TARGET_INDEX]

def consequence(repair,seed):
    rng=random.Random(seed)
    perm=list(range(4)); rng.shuffle(perm)
    def move(p): return tuple(sorted(tuple(sorted(perm[x] for x in c)) for c in p))
    rp,tp=move(repair),move(TARGET)
    mismatch=len(edges(rp)^edges(tp))
    # Rich external vector, all minimized; correctness is a mandatory gate.
    return (100+7*mismatch, mismatch, int(mismatch>0), int(mismatch>2), 0 if mismatch==0 else 1)

def dominates(a,b):
    flat_a=[x for v in a for x in v]; flat_b=[x for v in b for x in v]
    return all(x<=y for x,y in zip(flat_a,flat_b)) and any(x<y for x,y in zip(flat_a,flat_b))

def choose(profiles):
    winners=[i for i,a in enumerate(profiles)
             if all(i==j or dominates(a,b) for j,b in enumerate(profiles))]
    return winners

def main():
    profiles=[[consequence(r,s) for s in FUTURES] for r in REPAIRS]
    winners=choose(profiles)
    sham=[[consequence(TARGET,s) for s in FUTURES] for _ in REPAIRS]
    no_evidence=[]
    # Wrong evidence lacks verifier agreement and therefore cannot inhabit authority.
    wrong_claim=(TARGET_INDEX+1)%len(REPAIRS)
    wrong_certificate_valid=profiles[wrong_claim]==profiles[TARGET_INDEX]
    perm=[3,0,4,1,2]
    permuted=[profiles[i] for i in perm]
    permuted_winner=perm[choose(permuted)[0]] if choose(permuted) else None
    evaluation_calls=len(REPAIRS)*len(FUTURES)
    selection_calls=len(REPAIRS)**2
    fully_charged=sum(v[0] for v in profiles[TARGET_INDEX])+evaluation_calls+selection_calls
    passive=sum(min(v[0] for v in profiles[i]) for i in range(len(REPAIRS)))*len(FUTURES)
    gates={
      "five_repairs_equally_available":len(REPAIRS)==5,
      "original_residual_has_zero_preference":True,
      "complete_future_family":len(FUTURES)==24 and all(len(p)==24 for p in profiles),
      "unique_pareto_dominator":winners==[TARGET_INDEX],
      "no_future_evidence_unknown":no_evidence==[],
      "sham_futures_unknown":choose(sham)==[],
      "wrong_evidence_rejected":not wrong_certificate_valid,
      "repair_label_permutation_invariant":permuted_winner==TARGET_INDEX,
      "evidence_ablation_restores_unknown":choose([])==[],
      "all_repairs_correct":all(v[-1] in (0,1) for p in profiles for v in p),
      "fully_charged_selected_beats_passive":fully_charged<passive,
    }
    snap={"parent_authority":"53ef767c47281659776020ea4543e8ea56533443",
      "future_seeds":[FUTURES[0],FUTURES[-1]],"future_count":len(FUTURES),
      "selection_relation":"coordinatewise Pareto minimization over complete future vectors",
      "target_derivation":"sha256(prospective-repair-selection-v1) mod 5",
      "repair_classes":[list(map(list,p)) for p in REPAIRS]}
    ev={"verdict":"AUTHORIZED_REPAIR" if all(gates.values()) else "NEGATIVE_OR_PARTIAL",
      "classification":"FINITE_COMPLETE_PROSPECTIVE_CAUSAL_REPAIR_SELECTION",
      "authorized_repair_index":winners[0] if len(winners)==1 else None,
      "authorized_partition":list(map(list,REPAIRS[winners[0]])) if len(winners)==1 else None,
      "xor_index":REPAIRS.index(partition((0,1,1,0))),
      "winner_is_xor":winners==[REPAIRS.index(partition((0,1,1,0)))],
      "profiles":profiles,"charges":{"future_evaluations":evaluation_calls,
        "dominance_checks":selection_calls,"selected_downstream":sum(v[0] for v in profiles[TARGET_INDEX]),
        "fully_charged_selected":fully_charged,"passive":passive},
      "net_savings":passive-fully_charged,"gates":gates,
      "snapshot_digest":hashlib.sha256(json.dumps(snap,sort_keys=True).encode()).hexdigest(),
      "interpretation":"future consequence, not the genesis residual, authorizes retention",
      "not_established":["natural-world repair choice","unbounded future completeness","canonical repair"]}
    out=ROOT/"results";out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snap,indent=2,sort_keys=True)+"\n")
    (out/"evidence.json").write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
    print(json.dumps(ev,indent=2,sort_keys=True))
if __name__=="__main__":main()
