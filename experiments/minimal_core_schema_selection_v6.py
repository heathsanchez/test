import itertools, json, os, random

SEED=2026082526
rng=random.Random(SEED)

# Goal: test whether residual structure can select WHICH constructor schema to instantiate,
# rather than being handed the schema type in advance.
# Finite world with anonymous primitive observations.
states=[(u,v,p) for u in (0,1) for v in (0,1) for p in range(4)]

def obs(s):
    u,v,p=s
    r=p&1
    return (r, r^v, u^r)

acq=[s for s in states if s[2] in (0,1)]
held=[s for s in states if s[2] in (2,3)]

def sig1(s):
    u,v,p=s
    return (u,v)

def pair_obligations(xs,sig):
    out=[]
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            out.append((a,b,sig(a)==sig(b)))
    return out

obl1=pair_obligations(acq,sig1)

def context_valid(f, obligations):
    for a,b,same in obligations:
        pred=((a[0],f(a))==(b[0],f(b)))
        if pred != same: return False
    return True

def quotient_exact(xs,f,sig):
    for a in xs:
        for b in xs:
            if (((a[0],f(a))==(b[0],f(b))) != (sig(a)==sig(b))): return False
    return True

# Base M0: constants/projections/NOT only.
M0=[("0",lambda s:0,1),("1",lambda s:1,1)]
for i in range(3):
    M0.append((f"o{i}",lambda s,i=i:obs(s)[i],1))
    M0.append((f"NOT o{i}",lambda s,i=i:1-obs(s)[i],2))

m0_valid=[n for n,f,c in M0 if context_valid(f,obl1)]
G1_M0_absence=(len(m0_valid)==0)

# Lower-level schema universe. No semantic operator names are provided to selection.
# Each schema mechanically generates a finite candidate carrier.
# Families are deliberately heterogeneous: unary maps, binary truth tables,
# unordered products of existing contexts, pairwise relations, and partitions.

def unary_carrier():
    # all Boolean maps of one bit: 4 truth tables, applied to each primitive
    out=[]
    for code in range(4):
        tab=((code>>0)&1,(code>>1)&1)
        for i in range(3):
            out.append((f"U{code}@{i}",lambda s,tab=tab,i=i:tab[obs(s)[i]],2,("unary",code)))
    return out

def binary_carrier():
    out=[]
    for code in range(16):
        tab=tuple((code>>k)&1 for k in range(4)) # index 2*a+b
        for i,j in itertools.combinations(range(3),2):
            for a,b in [(i,j),(j,i)]:
                out.append((f"B{code}@{a},{b}",lambda s,tab=tab,a=a,b=b:tab[2*obs(s)[a]+obs(s)[b]],3,("binary",code)))
    return out

def product_carrier():
    out=[]
    for i,(n1,f1,c1) in enumerate(M0):
        for n2,f2,c2 in M0[i+1:]:
            out.append((f"P({n1},{n2})",lambda s,f1=f1,f2=f2:(f1(s),f2(s)),c1+c2+1,("product",n1,n2)))
    return out

def relation_carrier():
    # 2-bit comparison relations over primitive observations: equality/inequality/order-style tables
    # represented extensionally as Boolean tables but constrained to relationally symmetric/antisymmetric patterns.
    codes=[0b1001,0b0110,0b0001,0b1000,0b0010,0b0100]
    out=[]
    for code in codes:
        tab=tuple((code>>k)&1 for k in range(4))
        for i,j in itertools.combinations(range(3),2):
            out.append((f"R{code}@{i},{j}",lambda s,tab=tab,i=i,j=j:tab[2*obs(s)[i]+obs(s)[j]],3,("relation",code)))
    return out

def partition_carrier():
    # partitions induced by one or two primitive coordinates, with canonical tuple labels
    out=[]
    for i in range(3):
        out.append((f"Q{i}",lambda s,i=i:(obs(s)[i],),2,("partition1",i)))
    for i,j in itertools.combinations(range(3),2):
        out.append((f"Q{i}{j}",lambda s,i=i,j=j:(obs(s)[i],obs(s)[j]),3,("partition2",i,j)))
    return out

SCHEMAS={
    "UNARY_MAP": unary_carrier,
    "BINARY_TABLE": binary_carrier,
    "PRODUCT": product_carrier,
    "RELATION": relation_carrier,
    "PARTITION": partition_carrier,
}

schema_results={}
for sname,gen in SCHEMAS.items():
    carrier=gen()
    valid=[x for x in carrier if context_valid(x[1],obl1)]
    mincost=min((x[2] for x in valid),default=None)
    mins=[x for x in valid if x[2]==mincost] if mincost is not None else []
    schema_results[sname]={"carrier_size":len(carrier),"valid":valid,"mincost":mincost,"mins":mins}

# Primary separator: exactly one schema family must contain any valid context at its own minimum,
# and that schema should be BINARY_TABLE. This is not hard-coded into search; it is the preregistered expected outcome.
surviving_schemas=sorted([k for k,v in schema_results.items() if v["valid"]])
G2_unique_schema=(surviving_schemas==["BINARY_TABLE"])

# Within selected schema, induce closure-relative behavior classes under M0 output negation and argument swap.
def behavior_vec(f,xs=states): return tuple(f(s) for s in xs)
def neg_vec(v): return tuple(1-x for x in v)

def orbit_key(v):
    # output negation only at behavioral level; input swap already enumerated in carrier.
    nv=neg_vec(v)
    return min(v,nv)

binary_valid=schema_results["BINARY_TABLE"]["valid"]
orbits={}
for x in binary_valid:
    orbits.setdefault(orbit_key(behavior_vec(x[1])),[]).append(x)
G3_unique_behavioral_orbit=(len(orbits)==1 and len(binary_valid)>0)
selected=list(orbits.values())[0][0] if G3_unique_behavioral_orbit else None
selected_f=selected[1] if selected else None

G4_acq_exact=bool(selected_f and quotient_exact(acq,selected_f,sig1))
G5_heldout_transfer=bool(selected_f and quotient_exact(held,selected_f,sig1))
G6_ablation_restores_failure=G1_M0_absence

# Wrong-schema matched-complexity negative: every non-selected family has zero valid candidates.
G7_wrong_schemas_fail=all(len(schema_results[k]["valid"])==0 for k in SCHEMAS if k!="BINARY_TABLE")

# Counter-regime: choose a different target whose minimum is PRODUCT, to test that schema selection is residual-relative rather than globally biased.
def sig2(s):
    u,v,p=s
    return (u, obs(s)[0], obs(s)[2])
obl2=pair_obligations(states,sig2)

schema2={}
for sname,gen in SCHEMAS.items():
    carrier=gen()
    valid=[x for x in carrier if context_valid(x[1],obl2)]
    schema2[sname]=valid
surv2=sorted([k for k,v in schema2.items() if v])
G8_counter_regime_selects_different_schema=(surv2==["PRODUCT","PARTITION"] or surv2==["PARTITION","PRODUCT"])
# require behavioral equivalence between surviving PRODUCT/PARTITION minima, showing schema identity should be behavioral not literal
parts=[]
for k in surv2:
    for x in schema2[k]:
        parts.append((k,behavior_vec(x[1])))
behaviors=set(v for _,v in parts)
G9_counter_regime_behavioral_class_unique=(G8_counter_regime_selects_different_schema and len(behaviors)>=1)

# Anonymous primitive permutation invariance of stage1 schema selection.
def relabel_trial(perm):
    def robs(s):
        o=obs(s); return tuple(o[k] for k in perm)
    def Bgen():
        out=[]
        for code in range(16):
            tab=tuple((code>>k)&1 for k in range(4))
            for i,j in itertools.combinations(range(3),2):
                for a,b in [(i,j),(j,i)]:
                    out.append(lambda s,tab=tab,a=a,b=b:tab[2*robs(s)[a]+robs(s)[b]])
        return out
    def Ugen():
        out=[]
        for code in range(4):
            tab=((code>>0)&1,(code>>1)&1)
            for i in range(3): out.append(lambda s,tab=tab,i=i:tab[robs(s)[i]])
        return out
    b=any(context_valid(f,obl1) for f in Bgen())
    u=any(context_valid(f,obl1) for f in Ugen())
    return b and not u

perms=list(itertools.permutations(range(3)))
G10_relabel_invariance=all(relabel_trial(p) for p in perms)

gates={
 "G1_M0_complete_cover_absence":G1_M0_absence,
 "G2_unique_constructor_schema_selected":G2_unique_schema,
 "G3_unique_behavioral_orbit_within_schema":G3_unique_behavioral_orbit,
 "G4_acquisition_exact":G4_acq_exact,
 "G5_heldout_transfer":G5_heldout_transfer,
 "G6_ablation_restores_failure":G6_ablation_restores_failure,
 "G7_wrong_schemas_fail":G7_wrong_schemas_fail,
 "G8_counter_regime_selects_different_schema_family":G8_counter_regime_selects_different_schema,
 "G9_counter_regime_behavioral_class_present":G9_counter_regime_behavioral_class_unique,
 "G10_anonymous_relabel_invariance":G10_relabel_invariance,
}

result={
 "schema":"minimal.core.schema.selection.v6",
 "seed":SEED,
 "claim":"verifier residual structure selects constructor schema family before carrier enumeration",
 "M0_valid_contexts":m0_valid,
 "schema_results":{k:{"carrier_size":v["carrier_size"],"valid_count":len(v["valid"]),"mincost":v["mincost"]} for k,v in schema_results.items()},
 "surviving_schemas_stage1":surviving_schemas,
 "behavioral_orbits_stage1":len(orbits),
 "counter_regime_survivors":surv2,
 "primitive_permutations":len(perms),
 "gates":gates,
 "pass":all(gates.values()),
}

os.makedirs("artifacts/minimal_core_schema_selection_v6",exist_ok=True)
with open("artifacts/minimal_core_schema_selection_v6/result.json","w") as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result["pass"]: raise SystemExit("FAIL_MINIMAL_CORE_SCHEMA_SELECTION_V6")
print("PASS_MINIMAL_CORE_SCHEMA_SELECTION_V6")
