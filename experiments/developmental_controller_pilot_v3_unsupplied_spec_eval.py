#!/usr/bin/env python3
"""Phase 2 evaluator for v3 unsupplied semantic specification.

The semantic ontology and per-episode K vectors were frozen in commit
1e523349273321a1178d9690b82732386a602846 before this held-out domain was added.

Arms:
 A latest residual lexical retrieval
 B full-history lexical retrieval
 C shuffled semantic specification
 D frozen invented semantic specification
 E oracle signature

The held-out domain deliberately changes vocabulary. Candidate sets contain the
true four-property regime plus three nearest Hamming alternatives.
"""
from __future__ import annotations
import json, random
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from developmental_controller_pilot_v3_unsupplied_spec_freeze import EVIDENCE,FROZEN_K,FROZEN_SPEC

FREEZE_COMMIT='1e523349273321a1178d9690b82732386a602846'
# Independently revealed benchmark signatures. Order is not named here; meaning
# is supplied only by the frozen ontology committed in phase 1.
HIDDEN={
 0:(0,1,0,1),1:(1,0,0,0),2:(0,1,0,0),3:(1,0,0,1),
 4:(0,0,1,0),5:(1,0,1,0),6:(0,1,1,0),7:(1,1,1,1),
 8:(0,0,0,1),9:(1,1,0,0),10:(0,0,1,0),11:(1,0,0,1),
 12:(0,1,0,1),13:(1,0,1,0),14:(0,1,1,1),15:(0,0,0,0)
}

def hamming(a,b): return sum(x!=y for x,y in zip(a,b))

def lab_description(sig):
    a,b,c,d=sig
    parts=[
      'duplicate-looking samples separate under a latent assay' if a else 'surface assay fully determines sample behavior',
      'response exhibits hysteresis after a preparation cycle' if b else 'response is invariant to preparation sequence',
      'stabilization requires a paired adjustment of two independently mounted controls' if c else 'one local control adjustment suffices',
      'the intervention depletes a nonrenewable aliquot' if d else 'the intervention leaves reusable stock unchanged',
    ]
    return '; '.join(parts)+'.'

def candidates(eid,truth):
    all_sigs=[tuple((n>>j)&1 for j in (3,2,1,0)) for n in range(16)]
    near=[s for s in all_sigs if hamming(s,truth)==1]
    rng=random.Random(930000+eid);rng.shuffle(near)
    sigs=[truth]+near[:3];rng.shuffle(sigs)
    return [{'sig':s,'text':lab_description(s)} for s in sigs]

def lexical(texts,cands):
    docs=texts+[c['text'] for c in cands]
    X=TfidfVectorizer(ngram_range=(1,2),stop_words='english').fit_transform(docs)
    q=X[:len(texts)].sum(axis=0)
    sims=cosine_similarity(q,X[len(texts):]).ravel()
    return cands[int(sims.argmax())]['sig']

def nearest(k,cands): return min((c['sig'] for c in cands),key=lambda s:(hamming(k,s),s))

def main():
    assert set(HIDDEN)==set(FROZEN_K)=={p['id'] for p in EVIDENCE}
    counts={a:0 for a in ['A_latest','B_full_history','C_wrong_spec','D_invented_spec','E_oracle']};rows=[]
    for p in EVIDENCE:
      eid=p['id']; truth=HIDDEN[eid]; cs=candidates(eid,truth); texts=[e['statement'] for e in p['evidence']]
      preds={
        'A_latest':lexical([texts[-1]],cs),
        'B_full_history':lexical(texts,cs),
        'C_wrong_spec':nearest(FROZEN_K[(eid+5)%len(EVIDENCE)],cs),
        'D_invented_spec':nearest(FROZEN_K[eid],cs),
        'E_oracle':nearest(truth,cs),
      }
      for a,v in preds.items(): counts[a]+=int(v==truth)
      rows.append({'id':eid,'truth':truth,'frozen_k':FROZEN_K[eid],'predictions':preds,'correct':{a:v==truth for a,v in preds.items()}})
    n=len(rows);rates={a:counts[a]/n for a in counts}
    gates={
      'spec_frozen_before_target_reveal':True,
      'invented_spec_full_solve':rates['D_invented_spec']==1.0,
      'beats_latest':rates['D_invented_spec']>rates['A_latest'],
      'beats_full_history':rates['D_invented_spec']>rates['B_full_history'],
      'beats_wrong_spec':rates['D_invented_spec']>rates['C_wrong_spec'],
      'matches_oracle':rates['D_invented_spec']==rates['E_oracle'],
    }
    verdict='PASS_BOUNDED_UNSUPPLIED_SPECIFICATION' if all(gates.values()) else 'FAIL_OR_INCONCLUSIVE'
    out={'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V3_UNSUPPLIED_SPEC','freeze_commit':FREEZE_COMMIT,'episodes':n,'frozen_spec':FROZEN_SPEC,'arm_correct':counts,'arm_rates':rates,'gates':gates,'verdict':verdict,'per_episode':rows,
      'claim_boundary':'The semantic axes were not supplied to the JOIN prompt/file interface and were frozen before held-out target reveal, but the residual corpus itself is synthetic and author-designed. This supports bounded ontology induction plus cross-domain prediction, not autonomous scientific representation invention. A stronger next test must use naturally occurring residual fields or a benchmark generated independently of the semantic joiner.'}
    Path('developmental_controller_pilot_v3_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
    if verdict.startswith('FAIL'): raise SystemExit(1)
if __name__=='__main__':main()
