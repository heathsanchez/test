import itertools, json, os, random

SEED=2026082523
rng=random.Random(SEED)

# Raw world: hidden target bit v is deliberately not formable in M0 from the two anonymous
# observations o0,o1 using the frozen unary-only grammar.  Their XOR equals v.
states=[(u,v,p) for u in (0,1) for v in (0,1) for p in range(4)]

def obs(s):
    u,v,p=s
    # anonymous primitive observations; neither alone identifies v
    return (u ^ v, u, p & 1)

# Acquisition/held-out split is by presentation coordinate; constructor never sees held-out obligations.
acq=[s for s in states if s[2] in (0,1)]
held=[s for s in states if s[2] in (2,3)]

# Desired verifier-relative substitutability for stage 1: same iff (u,v) agree.
def target_sig1(s):
    u,v,p=s
    return (u,v)

def pair_obligations(xs, sig):
    out=[]
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            out.append((a,b, sig(a)==sig(b)))
    return out

obl1=pair_obligations(acq,target_sig1)

# M0: constants, anonymous primitive projections, negation only. No binary composition.
def m0_exprs():
    fs=[]
    fs.append(("0", lambda s:0,1))
    fs.append(("1", lambda s:1,1))
    for i in range(3):
        fs.append((f"o{i}", lambda s,i=i:obs(s)[i],1))
        fs.append((f"NOT o{i}", lambda s,i=i:1-obs(s)[i],2))
    return fs

M0=m0_exprs()

# A candidate context is added to the current representation (which already retains u).
# It is valid iff equality of (u,ctx) matches every acquisition SAME/DIFFERENT obligation.
def context_valid(f, obligations):
    for a,b,same in obligations:
        pred=((a[0],f(a))==(b[0],f(b)))
        if pred != same:
            return False
    return True

m0_valid=[name for name,f,c in M0 if context_valid(f,obl1)]
G1_M0_complete_absence=(len(m0_valid)==0)

# Meta-grammar does NOT directly contain the target context. It contains candidate grammar edits:
# add one binary Boolean combinator to M0. We enumerate a deliberately symmetric family.
BINOPS={
    "AND": lambda a,b:a&b,
    "OR": lambda a,b:a|b,
    "XOR": lambda a,b:a^b,
    "XNOR": lambda a,b:1-(a^b),
    "NAND": lambda a,b:1-(a&b),
    "NOR": lambda a,b:1-(a|b),
    "A": lambda a,b:a,
    "B": lambda a,b:b,
}

# For each edit E(op), M1=M0+{op(x,y)} over anonymous primitives. Find minimum contexts satisfying residual.
def expanded_candidates(opname, op):
    c=[]
    for i,j in itertools.combinations(range(3),2):
        c.append((f"{opname}(o{i},o{j})", lambda s,i=i,j=j,op=op:op(obs(s)[i],obs(s)[j]),3))
        c.append((f"{opname}(o{j},o{i})", lambda s,i=i,j=j,op=op:op(obs(s)[j],obs(s)[i]),3))
    return c

edit_results=[]
for opname,op in BINOPS.items():
    vals=[]
    for name,f,cost in expanded_candidates(opname,op):
        if context_valid(f,obl1): vals.append((cost,name,f))
    if vals:
        vals.sort(key=lambda z:(z[0],z[1]))
        edit_results.append((vals[0][0],opname,vals[0][1],vals[0][2],len(vals)))

min_cost=min((r[0] for r in edit_results), default=None)
winners=[r for r in edit_results if r[0]==min_cost]
# XOR may have equivalent operand order, but the grammar EDIT (operator family) must be unique.
unique_ops=sorted(set(r[1] for r in winners))
G2_unique_minimal_grammar_edit=(unique_ops==["XOR"])
win=[r for r in winners if r[1]=="XOR"][0] if G2_unique_minimal_grammar_edit else None
winner_name=win[2] if win else None
winner_f=win[3] if win else None

# Verify revised quotient on acquisition + heldout continuations.
def quotient_exact(xs, f, sig):
    for a in xs:
        for b in xs:
            if (((a[0],f(a))==(b[0],f(b))) != (sig(a)==sig(b))):
                return False
    return True

G3_M1_forms_required_context= bool(winner_f and quotient_exact(acq,winner_f,target_sig1))
G4_heldout_transfer= bool(winner_f and quotient_exact(held,winner_f,target_sig1))

# Ablation = remove newly admitted binary combinator, returning exactly to M0 closure.
G5_ablation_restores_unformability = G1_M0_complete_absence

# Wrong-edit matched-complexity controls must fail to form an exact context.
wrong_success=[]
for opname,op in BINOPS.items():
    if opname=="XOR": continue
    ok=any(context_valid(f,obl1) for _,f,_ in expanded_candidates(opname,op))
    wrong_success.append((opname,ok))
G6_wrong_edits_fail=not any(ok for _,ok in wrong_success)

# Stage 2: change continuation regime. Presentation parity now matters too, requiring a second bit.
def target_sig2(s):
    u,v,p=s
    return (u,v,p&1)
obl2=pair_obligations(states,target_sig2)

# M1 has XOR available, but only contexts built as single M0 primitive or one XOR expression.
M1_contexts=M0+expanded_candidates("XOR",BINOPS["XOR"])
# Single context appended to u cannot encode both v and p parity, so M1 must be insufficient.
m1_valid=[name for name,f,c in M1_contexts if context_valid(f,obl2)]
G7_regime2_M1_inadequate=(len(m1_valid)==0)

# Meta-expansion stage 2 admits PAIR, a typed product constructor combining two existing contexts.
# This is a constructor-language edit, not a new semantic primitive.
# Candidate components include M1 contexts; exhaust all unordered pairs and choose minimum total cost.
pair_candidates=[]
for i,(n1,f1,c1) in enumerate(M1_contexts):
    for n2,f2,c2 in M1_contexts[i+1:]:
        def pf(s,f1=f1,f2=f2): return (f1(s),f2(s))
        if context_valid(pf,obl2):
            pair_candidates.append((c1+c2+1,n1,n2,pf))
min2=min((x[0] for x in pair_candidates), default=None)
w2=[x for x in pair_candidates if x[0]==min2]
# Canonical behavioral winner should pair parity o2 with an XOR representative of v.
def behavior_vector(f): return tuple(f(s) for s in states)
classes2={}
for x in w2:
    classes2.setdefault(behavior_vector(x[3]),[]).append(x)
G8_stage2_unique_behavioral_minimum=(len(classes2)==1 and len(w2)>0)
stage2_rep=w2[0] if w2 else None
G9_stage2_exact_and_ablation=bool(stage2_rep and quotient_exact(states,stage2_rep[3],target_sig2) and not any(context_valid(f,obl2) for _,f,_ in M1_contexts))

# Surface relabeling: permute primitive names/positions while preserving anonymous observations.
# Re-run stage1 operator-family selection and require XOR uniquely every time.
def relabel_trial(perm):
    def robs(s):
        o=obs(s); return tuple(o[k] for k in perm)
    def exps(opname,op):
        out=[]
        for i,j in itertools.combinations(range(3),2):
            out.append((lambda s,i=i,j=j,op=op:op(robs(s)[i],robs(s)[j])))
            out.append((lambda s,i=i,j=j,op=op:op(robs(s)[j],robs(s)[i])))
        return out
    good=[]
    for opname,op in BINOPS.items():
        if any(context_valid(f,obl1) for f in exps(opname,op)):
            good.append(opname)
    return sorted(set(good))==["XOR"]

perms=list(itertools.permutations(range(3)))
relabel_pass=all(relabel_trial(p) for p in perms)
G10_anonymous_relabel_invariance=relabel_pass

gates={
 "G1_M0_complete_cover_absence":G1_M0_complete_absence,
 "G2_unique_minimal_grammar_edit":G2_unique_minimal_grammar_edit,
 "G3_M1_forms_required_context":G3_M1_forms_required_context,
 "G4_heldout_transfer":G4_heldout_transfer,
 "G5_ablation_restores_unformability":G5_ablation_restores_unformability,
 "G6_matched_wrong_edits_fail":G6_wrong_edits_fail,
 "G7_regime2_M1_inadequate":G7_regime2_M1_inadequate,
 "G8_stage2_unique_behavioral_minimum":G8_stage2_unique_behavioral_minimum,
 "G9_stage2_exact_and_ablation":G9_stage2_exact_and_ablation,
 "G10_anonymous_relabel_invariance":G10_anonymous_relabel_invariance,
}

result={
 "schema":"minimal.core.constructor.expansion.v3",
 "seed":SEED,
 "core":"equivalence + verifier residual + CompleteCover + meta-grammar edit + coarsest revision",
 "M0_size":len(M0),
 "M0_valid_contexts":m0_valid,
 "meta_edit_families":list(BINOPS),
 "stage1_winning_operator": unique_ops[0] if len(unique_ops)==1 else unique_ops,
 "stage1_winner":winner_name,
 "stage1_edit_results":[{"op":r[1],"cost":r[0],"representative":r[2],"n_valid":r[4]} for r in edit_results],
 "stage2_M1_valid_contexts":m1_valid,
 "stage2_min_cost":min2,
 "stage2_min_representatives":[[x[1],x[2]] for x in w2],
 "stage2_behavioral_minima":len(classes2),
 "primitive_permutations":len(perms),
 "gates":gates,
 "pass":all(gates.values()),
}

os.makedirs("artifacts/minimal_core_constructor_expansion_v3",exist_ok=True)
with open("artifacts/minimal_core_constructor_expansion_v3/result.json","w") as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result["pass"]: raise SystemExit("FAIL_MINIMAL_CORE_CONSTRUCTOR_EXPANSION_V3")
print("PASS_MINIMAL_CORE_CONSTRUCTOR_EXPANSION_V3")
