import itertools, json, os, random

SEED=2026082524
rng=random.Random(SEED)

# Raw world.  u is already represented.  v is the hidden future-relevant bit.
# p is a presentation coordinate.  Anonymous observations are chosen so that
# neither primitive alone (even together with represented u) determines v,
# but XOR(o0,o1)=v.  This repairs the V3 fixture leakage where o0+u already did.
states=[(u,v,p) for u in (0,1) for v in (0,1) for p in range(4)]

def obs(s):
    u,v,p=s
    r=p&1
    return (r, r^v, u^r)

acq=[s for s in states if s[2] in (0,1)]
held=[s for s in states if s[2] in (2,3)]

def target_sig1(s):
    u,v,p=s
    return (u,v)

def target_sig2(s):
    u,v,p=s
    return (u,v,p&1)

def pair_obligations(xs,sig):
    out=[]
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            out.append((a,b,sig(a)==sig(b)))
    return out

obl1=pair_obligations(acq,target_sig1)
obl2=pair_obligations(states,target_sig2)

# M0 is exhaustively finite: constants, anonymous projections, and unary negation only.
def m0_exprs(observation=obs):
    fs=[("0",lambda s:0,1),("1",lambda s:1,1)]
    for i in range(3):
        fs.append((f"o{i}",lambda s,i=i:observation(s)[i],1))
        fs.append((f"NOT o{i}",lambda s,i=i:1-observation(s)[i],2))
    return fs

M0=m0_exprs()

def context_valid(f, obligations):
    # Current represented coordinate u remains installed; candidate context supplies
    # the missing quotient coordinate(s).
    for a,b,same in obligations:
        pred=((a[0],f(a))==(b[0],f(b)))
        if pred != same:
            return False
    return True

def quotient_exact(xs,f,sig):
    for a in xs:
        for b in xs:
            if (((a[0],f(a))==(b[0],f(b))) != (sig(a)==sig(b))):
                return False
    return True

m0_valid=[name for name,f,c in M0 if context_valid(f,obl1)]
G1_M0_complete_cover_absence=(len(m0_valid)==0)

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

def expanded_candidates(opname,op,observation=obs):
    c=[]
    for i,j in itertools.combinations(range(3),2):
        c.append((f"{opname}(o{i},o{j})",lambda s,i=i,j=j,op=op,observation=observation:op(observation(s)[i],observation(s)[j]),3))
        c.append((f"{opname}(o{j},o{i})",lambda s,i=i,j=j,op=op,observation=observation:op(observation(s)[j],observation(s)[i]),3))
    return c

# Closure-relative identity: because NOT is already in M0, XOR and XNOR are one
# capability orbit.  Argument permutation is also quotiented because operand order
# is presentation-only for these symmetric Boolean operations.
def op_orbit(opname):
    if opname in ("XOR","XNOR"): return "PARITY_ORBIT"
    if opname in ("AND","NAND"): return "AND_ORBIT"
    if opname in ("OR","NOR"): return "OR_ORBIT"
    if opname in ("A","B"): return "PROJECTION_ORBIT"
    return opname

edit_results=[]
for opname,op in BINOPS.items():
    vals=[]
    for name,f,cost in expanded_candidates(opname,op):
        if context_valid(f,obl1): vals.append((cost,name,f))
    if vals:
        vals.sort(key=lambda z:(z[0],z[1]))
        edit_results.append((vals[0][0],opname,op_orbit(opname),vals[0][1],vals[0][2],len(vals)))

min_cost=min((r[0] for r in edit_results),default=None)
winners=[r for r in edit_results if r[0]==min_cost]
winning_orbits=sorted(set(r[2] for r in winners))
G2_unique_minimal_capability_class=(winning_orbits==["PARITY_ORBIT"])
# Pick a canonical representative only for downstream evaluation; scientific identity is the orbit.
parity_winners=[r for r in winners if r[2]=="PARITY_ORBIT"]
win=parity_winners[0] if G2_unique_minimal_capability_class and parity_winners else None
winner_name=win[3] if win else None
winner_f=win[4] if win else None

G3_M1_forms_required_context=bool(winner_f and quotient_exact(acq,winner_f,target_sig1))
G4_heldout_transfer=bool(winner_f and quotient_exact(held,winner_f,target_sig1))
G5_ablation_restores_unformability=G1_M0_complete_cover_absence

# Wrong capability-class controls: no non-parity orbit may satisfy the acquisition obligations.
wrong_orbit_success=sorted(set(r[2] for r in edit_results if r[2] != "PARITY_ORBIT"))
G6_wrong_capability_classes_fail=(len(wrong_orbit_success)==0)

# Stage 2.  M1 admits the entire parity orbit (XOR/XNOR); a single Boolean context
# cannot encode both v and presentation parity, so M1 must again be insufficient.
M1_contexts=M0+expanded_candidates("XOR",BINOPS["XOR"])+expanded_candidates("XNOR",BINOPS["XNOR"])
m1_valid=[name for name,f,c in M1_contexts if context_valid(f,obl2)]
G7_regime2_M1_inadequate=(len(m1_valid)==0)

# Frozen meta-edit 2: PAIR/product constructor over existing M1 contexts.
pair_candidates=[]
for i,(n1,f1,c1) in enumerate(M1_contexts):
    for n2,f2,c2 in M1_contexts[i+1:]:
        def pf(s,f1=f1,f2=f2): return (f1(s),f2(s))
        if context_valid(pf,obl2): pair_candidates.append((c1+c2+1,n1,n2,pf))
min2=min((x[0] for x in pair_candidates),default=None)
w2=[x for x in pair_candidates if x[0]==min2]

def partition_signature(f,xs=states):
    # Canonical partition independent of literal tuple labels.
    groups={}
    for idx,s in enumerate(xs):
        key=(s[0],f(s))
        groups.setdefault(key,[]).append(idx)
    return tuple(sorted(tuple(v) for v in groups.values()))

classes2={}
for x in w2:
    classes2.setdefault(partition_signature(x[3]),[]).append(x)
G8_stage2_unique_behavioral_minimum=(len(classes2)==1 and len(w2)>0)
stage2_rep=w2[0] if w2 else None
G9_stage2_exact_and_ablation=bool(stage2_rep and quotient_exact(states,stage2_rep[3],target_sig2) and not m1_valid)

# Anonymous primitive permutation invariance. Rebuild M0 and edits under every permutation;
# require M0 absence and the same unique PARITY_ORBIT winner.
def relabel_trial(perm):
    def robs(s):
        o=obs(s); return tuple(o[k] for k in perm)
    RM0=m0_exprs(robs)
    if any(context_valid(f,obl1) for _,f,_ in RM0): return False
    good=[]
    for opname,op in BINOPS.items():
        vals=[f for _,f,_ in expanded_candidates(opname,op,robs) if context_valid(f,obl1)]
        if vals: good.append(op_orbit(opname))
    return sorted(set(good))==["PARITY_ORBIT"]

perms=list(itertools.permutations(range(3)))
G10_anonymous_relabel_invariance=all(relabel_trial(p) for p in perms)

gates={
 "G1_M0_complete_cover_absence":G1_M0_complete_cover_absence,
 "G2_unique_minimal_capability_class":G2_unique_minimal_capability_class,
 "G3_M1_forms_required_context":G3_M1_forms_required_context,
 "G4_heldout_transfer":G4_heldout_transfer,
 "G5_ablation_restores_unformability":G5_ablation_restores_unformability,
 "G6_wrong_capability_classes_fail":G6_wrong_capability_classes_fail,
 "G7_regime2_M1_inadequate":G7_regime2_M1_inadequate,
 "G8_stage2_unique_behavioral_minimum":G8_stage2_unique_behavioral_minimum,
 "G9_stage2_exact_and_ablation":G9_stage2_exact_and_ablation,
 "G10_anonymous_relabel_invariance":G10_anonymous_relabel_invariance,
}

result={
 "schema":"minimal.core.constructor.expansion.v4",
 "seed":SEED,
 "claim_unit":"closure-relative capability class, not literal operator",
 "M0_size":len(M0),
 "M0_valid_contexts":m0_valid,
 "stage1_edit_results":[{"op":r[1],"orbit":r[2],"cost":r[0],"representative":r[3],"n_valid":r[5]} for r in edit_results],
 "stage1_winning_orbits":winning_orbits,
 "stage1_canonical_representative":winner_name,
 "stage2_M1_valid_contexts":m1_valid,
 "stage2_min_cost":min2,
 "stage2_behavioral_minima":len(classes2),
 "stage2_min_representatives":[[x[1],x[2]] for x in w2],
 "primitive_permutations":len(perms),
 "gates":gates,
 "pass":all(gates.values()),
}

os.makedirs("artifacts/minimal_core_constructor_expansion_v4",exist_ok=True)
with open("artifacts/minimal_core_constructor_expansion_v4/result.json","w") as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result["pass"]: raise SystemExit("FAIL_MINIMAL_CORE_CONSTRUCTOR_EXPANSION_V4")
print("PASS_MINIMAL_CORE_CONSTRUCTOR_EXPANSION_V4")
