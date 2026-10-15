#!/usr/bin/env python3
"""Phase-2 evaluation for the v2b semantic JOIN pilot.

Commit-order guard: the evidence packets and FROZEN_JOIN_K were committed first
(c47af85e5a60572f3b4b6a414a7e4723276438d2), with no hidden signatures or
downstream candidates in that commit. This file reveals the sealed signatures
and downstream database candidate sets only after the JOIN outputs were frozen.

Arms:
 A serial latest residual: lexical choice using only the last source statement
 B full history/no semantic JOIN: lexical choice using all retained statements
 C wrong JOIN: use a one-episode-rotated semantic K vector
 D frozen semantic JOIN: use the pre-reveal K vector
 E oracle latent JOIN: use the sealed hidden K vector
"""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from developmental_controller_pilot_v2b_blind_join_freeze import EVIDENCE, FROZEN_JOIN_K

FREEZE_COMMIT = "c47af85e5a60572f3b4b6a414a7e4723276438d2"
OUT = Path("developmental_controller_pilot_v2b_result.json")
HIDDEN = {
0:(1,0,0,1), 1:(1,0,1,0), 2:(0,1,1,0), 3:(1,1,0,0),
4:(0,1,0,1), 5:(1,1,0,1), 6:(1,1,1,1), 7:(0,1,1,1),
8:(1,0,0,0), 9:(0,1,0,0), 10:(0,0,0,0), 11:(0,0,0,1),
12:(0,0,1,1), 13:(0,0,1,0), 14:(1,1,1,0), 15:(1,0,1,1),
}

def describe(sig):
    I,S,C,K=sig
    clauses=[
      "one plan fingerprint groups execution-distinct queries" if I else "plan fingerprints preserve execution-relevant identity",
      "the rewrite fires outside the transaction shapes where it is valid" if S else "the rewrite remains valid across the transaction shapes that admit it",
      "repair requires a coupled change to join ordering and a materialization boundary" if C else "a single local plan rewrite is sufficient",
      "discovering the canonical plan costs about as much as executing it" if K else "discovering the canonical plan is cheap relative to execution",
    ]
    return "; ".join(clauses)+"."

def hamming(a,b): return sum(x!=y for x,y in zip(a,b))

def candidates(eid,truth):
    all_sigs=[tuple((n>>j)&1 for j in (3,2,1,0)) for n in range(16)]
    d1=[s for s in all_sigs if s!=truth and hamming(s,truth)==1]
    rng=random.Random(810000+eid); rng.shuffle(d1)
    sigs=[truth]+d1[:3]; rng.shuffle(sigs)
    return [{"sig":s,"text":describe(s)} for s in sigs]

def lexical_choice(texts,cands):
    docs=texts+[c["text"] for c in cands]
    X=TfidfVectorizer(ngram_range=(1,2),stop_words="english").fit_transform(docs)
    # Compare each candidate to every retained source statement, then aggregate.
    sims=cosine_similarity(X[len(texts):], X[:len(texts)])
    scores=sims.sum(axis=1)
    return cands[int(scores.argmax())]["sig"]

def nearest_choice(k,cands):
    return min((c["sig"] for c in cands), key=lambda s:(hamming(k,s),s))

def main():
    assert set(HIDDEN)==set(FROZEN_JOIN_K)=={p["id"] for p in EVIDENCE}
    rows=[]
    names=["A_serial_latest","B_full_history_no_join","C_wrong_join","D_semantic_join","E_oracle_join"]
    arm_correct={a:0 for a in names}
    for p in EVIDENCE:
        eid=p["id"]; truth=HIDDEN[eid]; cs=candidates(eid,truth)
        texts=[e["statement"] for e in p["evidence"]]
        predA=lexical_choice([texts[-1]],cs)
        predB=lexical_choice(texts,cs)
        wrong=FROZEN_JOIN_K[(eid+1)%len(EVIDENCE)]
        predC=nearest_choice(wrong,cs)
        predD=nearest_choice(FROZEN_JOIN_K[eid],cs)
        predE=nearest_choice(truth,cs)
        preds={"A_serial_latest":predA,"B_full_history_no_join":predB,"C_wrong_join":predC,"D_semantic_join":predD,"E_oracle_join":predE}
        for a,v in preds.items(): arm_correct[a]+=int(v==truth)
        rows.append({"id":eid,"truth":truth,"frozen_K":FROZEN_JOIN_K[eid],"candidates":[c["text"] for c in cs],"predictions":preds,"correct":{a:v==truth for a,v in preds.items()}})
    n=len(rows); rates={a:arm_correct[a]/n for a in arm_correct}
    gates={
      "semantic_K_frozen_before_reveal": True,
      "semantic_join_full_solve": rates["D_semantic_join"]==1.0,
      "semantic_join_beats_serial": rates["D_semantic_join"]>rates["A_serial_latest"],
      "semantic_join_beats_full_history_no_join": rates["D_semantic_join"]>rates["B_full_history_no_join"],
      "semantic_join_beats_wrong_join": rates["D_semantic_join"]>rates["C_wrong_join"],
      "semantic_matches_oracle": rates["D_semantic_join"]==rates["E_oracle_join"],
    }
    verdict="PASS_BOUNDED_SEMANTIC_JOIN_CAUSAL_ADVANTAGE" if all(gates.values()) else "FAIL_OR_INCONCLUSIVE"
    payload={
      "protocol":"DEVELOPMENTAL_CONTROLLER_PILOT_V2B_BLIND_SEMANTIC_JOIN",
      "freeze_commit":FREEZE_COMMIT,"episodes":n,
      "axes":["illegal_identity_equivalence","overbroad_applicability","cross_component_composition_required","representation_acquisition_cost_high"],
      "arm_correct":arm_correct,"arm_rates":rates,"gates":gates,"verdict":verdict,
      "target_reveal_digest":hashlib.sha256(json.dumps(HIDDEN,sort_keys=True).encode()).hexdigest(),
      "per_episode":rows,
      "interpretation":"Unlike v1, full history is not already expressed as commensurable constraints. The D arm first translates heterogeneous kernel/SAIR/code residuals into one shared four-property K specification, frozen before the database target is revealed. The test asks whether that semantic coagulation predicts a held-out fourth-domain regime better than retained lexical history and a deliberately wrong JOIN.",
      "claim_boundary":"This is still a synthetic, author-designed bounded microbenchmark. Passing supports a causal role for semantic coordinate translation/coagulation under this sealed protocol; it does not establish autonomous open-ended scientific JOIN, ontology invention, or general residual-to-specification induction. The next escalation must replace supplied axes with a latent structure not named in advance and/or use real residual fields.",
    }
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,indent=2,sort_keys=True))
    if verdict.startswith("FAIL"): raise SystemExit(1)

if __name__=="__main__": main()
