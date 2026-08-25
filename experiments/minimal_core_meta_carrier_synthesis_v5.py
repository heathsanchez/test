import itertools, json, os

SEED=2026082525

# Parent fixture: same finite world as V4, but REMOVE the hand-written binary
# operator menu.  The only supplied meta-substrate is an extensional 2-input
# Boolean table with four anonymous output slots.  The carrier of possible edits
# is generated exhaustively as all 2^4 tables.
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
    return [(a,b,sig(a)==sig(b)) for i,a in enumerate(xs) for b in xs[i+1:]]

obl1=pair_obligations(acq,target_sig1)
obl2=pair_obligations(states,target_sig2)

def m0_exprs(observation=obs):
    fs=[("0",lambda s:0,1),("1",lambda s:1,1)]
    for i in range(3):
        fs.append((f"o{i}",lambda s,i=i,observation=observation:observation(s)[i],1))
        fs.append((f"NOT o{i}",lambda s,i=i,observation=observation:1-observation(s)[i],2))
    return fs

M0=m0_exprs()

def context_valid(f, obligations):
    for a,b,same in obligations:
        pred=((a[0],f(a))==(b[0],f(b)))
        if pred!=same: return False
    return True

def quotient_exact(xs,f,sig):
    return all((((a[0],f(a))==(b[0],f(b)))==(sig(a)==sig(b))) for a in xs for b in xs)

# G1: old constructor language really cannot form the needed context.
m0_valid=[n for n,f,c in M0 if context_valid(f,obl1)]
G1_M0_complete_cover_absence=(len(m0_valid)==0)

# Lower-level meta-carrier constructor: four anonymous bits define a complete
# truth table on inputs 00,01,10,11.  No named AND/OR/XOR/etc. list exists.
def table_fn(code):
    bits=tuple((code>>k)&1 for k in range(4))
    return lambda a,b,bits=bits:bits[(a<<1)|b]

def table_bits(code): return tuple((code>>k)&1 for k in range(4))

GENERATED_TABLES=list(range(16))
G2_full_meta_carrier_generated=(len(GENERATED_TABLES)==16 and len(set(table_bits(c) for c in GENERATED_TABLES))==16)

# Closure-relative identity is COMPUTED, not named.  M0 supplies input/output NOT;
# presentation symmetry supplies argument swap.  Canonical orbit key is the least
# truth-table code reachable under these transformations.
def transformed_code(code,na,nb,swap,no):
    f=table_fn(code)
    out=[0]*4
    for a,b in itertools.product((0,1),repeat=2):
        x,y=a^na,b^nb
        if swap: x,y=y,x
        z=f(x,y)^no
        out[(a<<1)|b]=z
    c=0
    for k,z in enumerate(out): c|=(z&1)<<k
    return c

def orbit(code):
    return frozenset(transformed_code(code,na,nb,sw,no)
                     for na,nb,sw,no in itertools.product((0,1),(0,1),(0,1),(0,1)))

def orbit_key(code): return min(orbit(code))

all_orbits={orbit_key(c):orbit(c) for c in GENERATED_TABLES}
G3_orbits_induced_from_old_closure=(len(all_orbits)>=2 and all(c in all_orbits[orbit_key(c)] for c in GENERATED_TABLES))

# New binary table may consume any anonymous primitive observation pair.  The
# carrier itself is extensional; semantic operator names are never used.
def candidates_for_code(code,observation=obs):
    f=table_fn(code); out=[]
    for i,j in itertools.combinations(range(3),2):
        for rev in (False,True):
            ii,jj=(j,i) if rev else (i,j)
            out.append((f"T{code:02d}(o{ii},o{jj})",
                        lambda s,ii=ii,jj=jj,f=f,observation=observation:f(observation(s)[ii],observation(s)[jj]),3))
    return out

survivors=[]
for code in GENERATED_TABLES:
    vals=[(n,f,c) for n,f,c in candidates_for_code(code) if context_valid(f,obl1)]
    if vals:
        vals.sort(key=lambda x:x[0])
        survivors.append((code,orbit_key(code),vals[0][0],vals[0][1],len(vals)))

surviving_orbits=sorted(set(x[1] for x in survivors))
G4_unique_residual_selected_orbit=(len(surviving_orbits)==1)
winner_orbit=surviving_orbits[0] if G4_unique_residual_selected_orbit else None
winner=next((x for x in survivors if x[1]==winner_orbit),None)
winner_f=winner[3] if winner else None

# Decode labels ONLY after selection for reporting; never used by selection logic.
def conventional_label(code):
    b=table_bits(code)
    known={
        (0,1,1,0):"XOR", (1,0,0,1):"XNOR",
        (0,0,0,1):"AND", (0,1,1,1):"OR",
        (1,1,1,0):"NAND", (1,0,0,0):"NOR"
    }
    return known.get(b,"UNNAMED")

selected_labels=sorted(set(conventional_label(c) for c in orbit(winner_orbit))) if winner_orbit is not None else []
G5_selected_orbit_is_parity_posthoc=("XOR" in selected_labels and "XNOR" in selected_labels)
G6_stage1_transfer_and_ablation=bool(winner_f and quotient_exact(acq,winner_f,target_sig1) and quotient_exact(held,winner_f,target_sig1) and G1_M0_complete_cover_absence)

# Matched-complexity carrier control: every generated table outside the selected
# orbit must fail the acquisition residual obligations.
wrong_survivors=[x for x in survivors if x[1]!=winner_orbit]
G7_wrong_generated_orbits_fail=(len(wrong_survivors)==0)

# Stage 2: install the selected orbit extension.  It must still be insufficient
# after the continuation regime changes.
M1=M0[:]
if winner_orbit is not None:
    for code in sorted(all_orbits[winner_orbit]):
        M1.extend(candidates_for_code(code))
m1_valid=[n for n,f,c in M1 if context_valid(f,obl2)]
G8_regime2_M1_inadequate=(len(m1_valid)==0)

# Lower-level product-carrier constructor: rather than supplying one named PAIR
# edit, enumerate all unordered 2-context product candidates from M1.  Their
# behavioral partition is what matters.
def partition_signature(f,xs=states):
    groups={}
    for idx,s in enumerate(xs): groups.setdefault((s[0],f(s)),[]).append(idx)
    return tuple(sorted(tuple(v) for v in groups.values()))

products=[]
for i,(n1,f1,c1) in enumerate(M1):
    for n2,f2,c2 in M1[i+1:]:
        def pf(s,f1=f1,f2=f2): return (f1(s),f2(s))
        if context_valid(pf,obl2): products.append((c1+c2+1,n1,n2,pf))
min_cost=min((x[0] for x in products),default=None)
mins=[x for x in products if x[0]==min_cost]
beh={}
for x in mins: beh.setdefault(partition_signature(x[3]),[]).append(x)
G9_generated_product_carrier_unique_behavioral_minimum=(len(beh)==1 and len(mins)>0)
rep=mins[0] if mins else None
G10_recursive_growth_exact_and_ablatable=bool(rep and quotient_exact(states,rep[3],target_sig2) and not m1_valid)

# Strong presentation check: every permutation of anonymous primitive channels must
# regenerate a single selected closure-relative orbit and preserve transfer.
def relabel_trial(perm):
    def robs(s):
        o=obs(s); return tuple(o[k] for k in perm)
    RM0=m0_exprs(robs)
    if any(context_valid(f,obl1) for _,f,_ in RM0): return False
    good=[]
    reps=[]
    for code in GENERATED_TABLES:
        vals=[(n,f,c) for n,f,c in candidates_for_code(code,robs) if context_valid(f,obl1)]
        if vals:
            good.append(orbit_key(code)); reps.append(vals[0][1])
    if len(set(good))!=1: return False
    return any(quotient_exact(held,f,target_sig1) for f in reps)

perms=list(itertools.permutations(range(3)))
G11_anonymous_relabel_invariance=all(relabel_trial(p) for p in perms)

gates={
 "G1_M0_complete_cover_absence":G1_M0_complete_cover_absence,
 "G2_full_extensional_meta_carrier_generated":G2_full_meta_carrier_generated,
 "G3_closure_relative_orbits_induced":G3_orbits_induced_from_old_closure,
 "G4_unique_residual_selected_orbit":G4_unique_residual_selected_orbit,
 "G5_selected_orbit_decodes_to_parity_posthoc":G5_selected_orbit_is_parity_posthoc,
 "G6_stage1_transfer_and_ablation":G6_stage1_transfer_and_ablation,
 "G7_wrong_generated_orbits_fail":G7_wrong_generated_orbits_fail,
 "G8_regime2_M1_inadequate":G8_regime2_M1_inadequate,
 "G9_generated_product_carrier_unique_behavioral_minimum":G9_generated_product_carrier_unique_behavioral_minimum,
 "G10_recursive_growth_exact_and_ablatable":G10_recursive_growth_exact_and_ablatable,
 "G11_anonymous_relabel_invariance":G11_anonymous_relabel_invariance,
}

result={
 "schema":"minimal.core.meta.carrier.synthesis.v5",
 "seed":SEED,
 "claim":"meta-edit carrier generated from lower-level extensional structure; residual selects closure-relative capability orbit",
 "M0_size":len(M0),
 "M0_valid_contexts":m0_valid,
 "generated_truth_tables":len(GENERATED_TABLES),
 "generated_orbits":len(all_orbits),
 "surviving_table_codes":[x[0] for x in survivors],
 "surviving_orbits":surviving_orbits,
 "selected_orbit_members":sorted(all_orbits[winner_orbit]) if winner_orbit is not None else [],
 "selected_posthoc_labels":selected_labels,
 "stage2_M1_valid_contexts":m1_valid,
 "stage2_min_product_cost":min_cost,
 "stage2_min_product_count":len(mins),
 "stage2_behavioral_minima":len(beh),
 "primitive_permutations":len(perms),
 "gates":gates,
 "pass":all(gates.values()),
}

os.makedirs("artifacts/minimal_core_meta_carrier_synthesis_v5",exist_ok=True)
with open("artifacts/minimal_core_meta_carrier_synthesis_v5/result.json","w") as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result["pass"]: raise SystemExit("FAIL_MINIMAL_CORE_META_CARRIER_SYNTHESIS_V5")
print("PASS_MINIMAL_CORE_META_CARRIER_SYNTHESIS_V5")
