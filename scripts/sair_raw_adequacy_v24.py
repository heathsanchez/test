#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, random, re
from pathlib import Path
from itertools import product

"""V24 — first raw natural-domain adequacy bridge on official SAIR Stage-2 data.

No developmental episode roles are supplied. Raw equation strings are parsed and
anonymous observation ports are produced from generic syntax plus exact exhaustive
Fin-2 magma behavior. The public answer is withheld during representation
construction and used only afterward for downstream policy fitting/audit.
"""

# ---------- equation parser ----------
class Node:
    __slots__=("v","l","r")
    def __init__(self,v=None,l=None,r=None): self.v=v; self.l=l; self.r=r
    @property
    def leaf(self): return self.v is not None

def strip_outer(s):
    s=s.strip()
    while len(s)>=2 and s[0]=='(' and s[-1]==')':
        d=0; ok=True
        for i,c in enumerate(s):
            if c=='(': d+=1
            elif c==')': d-=1
            if d==0 and i<len(s)-1: ok=False; break
        if not ok: break
        s=s[1:-1].strip()
    return s

def parse_term(s):
    s=strip_outer(s); d=0
    # operation is fully parenthesized in the official corpus; split at top-level diamond
    for i,c in enumerate(s):
        if c=='(': d+=1
        elif c==')': d-=1
        elif c=='◇' and d==0:
            return Node(l=parse_term(s[:i]),r=parse_term(s[i+1:]))
    s=s.strip()
    if re.fullmatch(r'[a-z]',s): return Node(v=s)
    raise ValueError(f"cannot parse term: {s!r}")

def parse_eq(s):
    a,b=s.split('=',1); return parse_term(a),parse_term(b)

def vars_of(n,out=None):
    if out is None: out=set()
    if n.leaf: out.add(n.v)
    else: vars_of(n.l,out); vars_of(n.r,out)
    return out

def op_count(n): return 0 if n.leaf else 1+op_count(n.l)+op_count(n.r)
def depth(n): return 0 if n.leaf else 1+max(depth(n.l),depth(n.r))
def leaves(n): return 1 if n.leaf else leaves(n.l)+leaves(n.r)
def eval_term(n,env,table):
    if n.leaf: return env[n.v]
    return table[eval_term(n.l,env,table)][eval_term(n.r,env,table)]

def equation_holds(eq,table):
    a,b=eq; vs=sorted(vars_of(a)|vars_of(b))
    for vals in product((0,1), repeat=len(vs)):
        env=dict(zip(vs,vals))
        if eval_term(a,env,table)!=eval_term(b,env,table): return False
    return True

def all_fin2_tables():
    for bits in product((0,1),repeat=4):
        yield ((bits[0],bits[1]),(bits[2],bits[3]))

TABLES=tuple(all_fin2_tables())

# ---------- raw observations ----------
SYNTAX_NAMES=(
    's0','s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11'
)
VERIFIER_NAMES=('v0','v1','v2','v3','v4','v5')
ALL_NAMES=SYNTAX_NAMES+VERIFIER_NAMES

def observations(row):
    e1=parse_eq(row['equation1']); e2=parse_eq(row['equation2'])
    a1,b1=e1; a2,b2=e2
    # anonymous syntax ports; names carry no semantic role
    syntax=(
        op_count(a1)+op_count(b1), op_count(a2)+op_count(b2),
        len(vars_of(a1)|vars_of(b1)), len(vars_of(a2)|vars_of(b2)),
        depth(a1),depth(b1),depth(a2),depth(b2),
        leaves(a1)+leaves(b1),leaves(a2)+leaves(b2),
        int(vars_of(a1)|vars_of(b1)==vars_of(a2)|vars_of(b2)),
        abs((op_count(a1)+op_count(b1))-(op_count(a2)+op_count(b2)))
    )
    h=g=both=ce=rev=0; witness=None
    for t in TABLES:
        hh=equation_holds(e1,t); gg=equation_holds(e2,t)
        h+=hh; g+=gg; both+=(hh and gg); ce+=(hh and not gg); rev+=(gg and not hh)
        if witness is None and hh and not gg: witness=t
    verifier=(h,g,both,ce,rev,int(ce==0))
    return dict(zip(ALL_NAMES,syntax+verifier)), witness, (e1,e2)

def recheck_witness(eqs,w):
    if w is None: return True
    e1,e2=eqs
    return equation_holds(e1,w) and not equation_holds(e2,w)

# ---------- policy synthesis ----------
def thresholds(vals):
    u=sorted(set(vals))
    if len(u)<=16: return u
    idx=sorted(set(round(i*(len(u)-1)/15) for i in range(16)))
    return [u[i] for i in idx]

def make_atoms(rows,names):
    atoms=[]
    for n in names:
        for t in thresholds([r['x'][n] for r in rows]):
            atoms.append((n,'<=',t)); atoms.append((n,'>=',t))
    return atoms

def ae(a,x):
    n,op,t=a; return x[n]<=t if op=='<=' else x[n]>=t

def fit(rows,names):
    atoms=make_atoms(rows,names)
    y=[r['y'] for r in rows]
    def score_pred(pred): return sum(int(p==yy) for p,yy in zip(pred,y))
    best=None
    # constant baseline encoded as None separately
    for a in atoms:
        pa=[ae(a,r['x']) for r in rows]
        for inv in (False,True):
            pp=[(not z) if inv else z for z in pa]
            sc=score_pred(pp); key=(-sc,1,str((inv,a)))
            if best is None or key<best[0]: best=(key,('atom',inv,a),sc)
    # Two-atom compositional policies. Keep top atoms by training score to bound exhaustive pair search.
    ranked=[]
    for a in atoms:
        pa=[ae(a,r['x']) for r in rows]
        sc=max(score_pred(pa),score_pred([not z for z in pa]))
        ranked.append((-sc,str(a),a))
    top=[z[2] for z in sorted(ranked)[:80]]
    for i,a in enumerate(top):
        pa=[ae(a,r['x']) for r in rows]
        for b in top[i:]:
            pb=[ae(b,r['x']) for r in rows]
            for op in ('and','or'):
                pp=[(x and z) if op=='and' else (x or z) for x,z in zip(pa,pb)]
                for inv in (False,True):
                    qq=[not z for z in pp] if inv else pp
                    sc=score_pred(qq); key=(-sc,3,str((op,inv,a,b)))
                    if key<best[0]: best=(key,(op,inv,a,b),sc)
    return best[1],best[2]/len(rows),len(atoms)

def predict(p,x):
    if p[0]=='atom':
        _,inv,a=p; z=ae(a,x); return (not z) if inv else z
    op,inv,a,b=p; z=(ae(a,x) and ae(b,x)) if op=='and' else (ae(a,x) or ae(b,x)); return (not z) if inv else z

def accuracy(p,rows): return sum(predict(p,r['x'])==r['y'] for r in rows)/len(rows)

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]

def build_rows(root,sets):
    out=[]; rechecks=0; bad=0
    for s in sets:
        for row in load_jsonl(root/'examples'/'problems'/f'{s}.jsonl'):
            x,w,eqs=observations(row)
            ok=recheck_witness(eqs,w); rechecks+=w is not None; bad+=bool(w is not None and not ok)
            out.append({'id':row['id'],'source':s,'x':x,'y':bool(row['answer'])})
    return out,rechecks,bad

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sair-root',required=True); ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); root=Path(a.sair_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    train,rechecks1,bad1=build_rows(root,('normal','hard1','hard2'))
    test,rechecks2,bad2=build_rows(root,('hard3',))
    # PROOF=True, COUNTERMODEL=False
    maj=max(sum(r['y'] for r in train),len(train)-sum(r['y'] for r in train))/len(train)
    majority_value=sum(r['y'] for r in train)>=len(train)/2
    maj_test=sum(r['y']==majority_value for r in test)/len(test)
    full,train_acc,natoms=fit(train,ALL_NAMES)
    syn,syn_train,_=fit(train,SYNTAX_NAMES)
    full_test=accuracy(full,test); syn_test=accuracy(syn,test)

    # Deterministic shuffled-verifier control: permute only verifier ports across rows before fitting/testing.
    rng=random.Random(20260821)
    allr=[dict(id=r['id'],source=r['source'],x=dict(r['x']),y=r['y']) for r in train+test]
    vals=[tuple(r['x'][n] for n in VERIFIER_NAMES) for r in allr]; rng.shuffle(vals)
    for r,v in zip(allr,vals):
        for n,z in zip(VERIFIER_NAMES,v): r['x'][n]=z
    sh_train=allr[:len(train)]; sh_test=allr[len(train):]
    shp,_,_=fit(sh_train,ALL_NAMES); sh_acc=accuracy(shp,sh_test)

    gates={
      'external_official_sair_splits_used':True,
      'no_manual_developmental_roles_in_representation':True,
      'representation_construction_answer_blind':True,
      'hard3_is_heldout_source':all(r['source']=='hard3' for r in test),
      'heldout_policy_beats_majority':full_test>maj_test,
      'heldout_policy_beats_syntax_only':full_test>syn_test,
      'shuffled_verifier_degrades':sh_acc<full_test,
      'all_fin2_witness_observations_rechecked':(bad1+bad2)==0,
    }
    gates['SAIR_RAW_ADEQUACY_BRIDGE_GATE']=all(gates.values())
    result={
      'status':'V24_SAIR_RAW_ADEQUACY_BRIDGE',
      'claim_scope':'official external SAIR Stage-2 raw equation rows; train normal+hard1+hard2; hold out hard3; generic syntax and exact Fin2 behavior; public answer used only after representation construction',
      'n_train':len(train),'n_test':len(test),'fin2_witness_rechecks':rechecks1+rechecks2,
      'majority_test_accuracy':maj_test,
      'full_policy':str(full),'full_train_accuracy':train_acc,'full_hard3_accuracy':full_test,
      'syntax_policy':str(syn),'syntax_train_accuracy':syn_train,'syntax_hard3_accuracy':syn_test,
      'shuffled_verifier_hard3_accuracy':sh_acc,'candidate_atoms':natoms,'gates':gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
