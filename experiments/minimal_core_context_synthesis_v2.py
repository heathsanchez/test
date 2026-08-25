#!/usr/bin/env python3
import json, random
from itertools import combinations
from pathlib import Path

SEED = 2026082522
random.seed(SEED)

# 16 finite raw states. p is presentation; its low/high bits are initially nuisance.
STATES = [(u, v, p) for u in (0, 1) for v in (0, 1) for p in range(4)]
ACQ = [s for s in STATES if s[2] < 2]
HELD = [s for s in STATES if s[2] >= 2]

# Anonymous primitive observations. The missing stage-1 context v is NOT primitive:
#   o0 = u, o1 = u xor v  =>  v = o0 xor o1.
# o2/o3 are presentation bits.
def primitive_values(s):
    u, v, p = s
    return (u, u ^ v, p & 1, (p >> 1) & 1)

def eval_formula(f, s, perm=(0,1,2,3)):
    vals0 = primitive_values(s)
    vals = tuple(vals0[perm[i]] for i in range(4))
    op = f[0]
    if op == 'p': return vals[f[1]]
    if op == 'not': return 1 - eval_formula(f[1], s, perm)
    a = eval_formula(f[1], s, perm); b = eval_formula(f[2], s, perm)
    if op == 'xor': return a ^ b
    if op == 'and': return a & b
    if op == 'or': return a | b
    raise ValueError(op)

def fsize(f):
    if f[0] == 'p': return 1
    if f[0] == 'not': return 1 + fsize(f[1])
    return 1 + fsize(f[1]) + fsize(f[2])

def formula_str(f):
    if f[0] == 'p': return f"o{f[1]}"
    if f[0] == 'not': return f"NOT({formula_str(f[1])})"
    return f"({formula_str(f[1])} {f[0].upper()} {formula_str(f[2])})"

def grammar():
    ps = [('p', i) for i in range(4)]
    out = list(ps) + [('not', p) for p in ps]
    for op in ('xor','and','or'):
        for i,a in enumerate(ps):
            for b in ps[i+1:]:
                out.append((op,a,b))
    return sorted(out, key=lambda f:(fsize(f), formula_str(f)))

GRAMMAR = grammar()

# Pairwise verifier residual: only SAME/DIFFERENT under a hidden contextual outcome.
# The constructor never receives semantic names u/v/p or target labels.
def residual_obligations(states, outcome_fn):
    obs=[]
    for a,b in combinations(states,2):
        obs.append((a,b, outcome_fn(a)==outcome_fn(b)))
    return obs

def satisfies(f, obligations, perm=(0,1,2,3)):
    for a,b,must_same in obligations:
        if (eval_formula(f,a,perm)==eval_formula(f,b,perm)) != must_same:
            return False
    return True

def synthesize_minimal(obligations, perm=(0,1,2,3)):
    winners=[f for f in GRAMMAR if satisfies(f,obligations,perm)]
    if not winners: return None, []
    m=min(fsize(f) for f in winners)
    mins=[f for f in winners if fsize(f)==m]
    return mins[0], mins

def partition(key_fn):
    buckets={}
    for s in STATES:
        buckets.setdefault(key_fn(s),[]).append(s)
    return sorted([tuple(sorted(v)) for v in buckets.values()])

def exact_for_contexts(part, ctxs):
    # partition is list of blocks; exact iff every context is constant on each block.
    for block in part:
        for c in ctxs:
            vals={c(s) for s in block}
            if len(vals)!=1: return False
    return True

# Initial representation remembers u and a nuisance presentation bit, but aliases v.
P0 = partition(lambda s:(s[0], s[2]&1))
ctx_acq = lambda s:s[1]                   # hidden acquisition continuation
ctx_h1 = lambda s:s[0]^s[1]              # held-out future continuation
ctx_h2 = lambda s:s[0]&s[1]              # held-out future continuation

# Stage 1: residuals are generated only on acquisition states and expose only
# pairwise contextual substitutability, not semantic labels.
obs1 = residual_obligations(ACQ, ctx_acq)
f1, mins1 = synthesize_minimal(obs1)
assert f1 is not None

# Coarsest revision keeps already-certified u and the synthesized context, and drops p nuisance.
P1 = partition(lambda s:(s[0], eval_formula(f1,s)))

# Controls.
wrong = ('xor',('p',0),('p',2))  # same syntactic size as the stage-1 winner
P_wrong = partition(lambda s:(s[0],eval_formula(wrong,s)))
P_noctx = partition(lambda s:(s[0],))

# Stage 2: new continuation makes presentation parity newly relevant.
ctx_new = lambda s:s[2]&1
obs2 = residual_obligations(STATES, ctx_new)
f2, mins2 = synthesize_minimal(obs2)
assert f2 is not None
P2 = partition(lambda s:(s[0],eval_formula(f1,s),eval_formula(f2,s)))
P2_ablate = P1

# Anonymous primitive-name relabeling: grammar is unchanged syntactically but primitive semantics
# are randomly permuted. A successful synthesis must still recover the same behavioral partitions.
relabel_ok=0
relabel_trials=128
for _ in range(relabel_trials):
    perm=list(range(4)); random.shuffle(perm); perm=tuple(perm)
    rf1,rmins1=synthesize_minimal(obs1,perm)
    rf2,rmins2=synthesize_minimal(obs2,perm)
    if rf1 is None or rf2 is None: continue
    rp1=partition(lambda s,p=perm,f=rf1:(s[0],eval_formula(f,s,p)))
    rp2=partition(lambda s,p=perm,a=rf1,b=rf2:(s[0],eval_formula(a,s,p),eval_formula(b,s,p)))
    if rp1==P1 and rp2==P2:
        relabel_ok += 1

# Gates.
all_reg1=[ctx_acq,ctx_h1,ctx_h2]
gates={
    'G1_initial_context_family_inadequate': not exact_for_contexts(P0,all_reg1),
    'G2_no_smaller_stage1_context_exists': fsize(f1)==3 and not any(satisfies(f,obs1) for f in GRAMMAR if fsize(f)<3),
    'G3_unique_minimal_context_synthesized': len(mins1)==1 and formula_str(f1)=='(o0 XOR o1)',
    'G4_stage1_context_recovers_hidden_substitutability': partition(lambda s:eval_formula(f1,s))==partition(lambda s:s[1]),
    'G5_revised_quotient_exact_acq_and_heldout': exact_for_contexts(P1,all_reg1) and len(P1)==4,
    'G6_context_ablation_restores_failure': not exact_for_contexts(P_noctx,all_reg1),
    'G7_matched_complexity_wrong_context_fails': fsize(wrong)==fsize(f1) and not exact_for_contexts(P_wrong,all_reg1),
    'G8_stage2_new_context_is_minimal': fsize(f2)==1 and len(mins2)==1 and partition(lambda s:eval_formula(f2,s))==partition(ctx_new),
    'G9_recursive_context_growth_refines_and_ablation_fails': len(P2)==8 and exact_for_contexts(P2,all_reg1+[ctx_new]) and not exact_for_contexts(P2_ablate,all_reg1+[ctx_new]),
    'G10_anonymous_primitive_relabel_invariance': relabel_ok==relabel_trials,
}

result={
    'schema':'minimal.core.context.synthesis.v2',
    'seed':SEED,
    'core':'equivalence relation + verifier residual + minimal context synthesis + coarsest revision',
    'raw_states':len(STATES),
    'grammar_size':len(GRAMMAR),
    'stage1':{
        'acquisition_states':len(ACQ),
        'winner':formula_str(f1),
        'winner_size':fsize(f1),
        'minimal_winner_count':len(mins1),
        'initial_classes':len(P0),
        'revised_classes':len(P1),
        'heldout_states':len(HELD),
    },
    'stage2':{
        'winner':formula_str(f2),
        'winner_size':fsize(f2),
        'minimal_winner_count':len(mins2),
        'revised_classes':len(P2),
        'ablation_classes':len(P2_ablate),
    },
    'relabel_trials':relabel_trials,
    'relabel_all_pass':relabel_ok==relabel_trials,
    'gates':gates,
    'pass':all(gates.values()),
}

outdir=Path('artifacts/minimal_core_context_synthesis_v2')
outdir.mkdir(parents=True,exist_ok=True)
(outdir/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']:
    raise SystemExit('FAIL_MINIMAL_CORE_CONTEXT_SYNTHESIS_V2')
print('PASS_MINIMAL_CORE_CONTEXT_SYNTHESIS_V2')
