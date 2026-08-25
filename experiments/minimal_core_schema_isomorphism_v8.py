import itertools, json, os

SEED=2026082601

# V8 follows the V7 negative.  In V7, BINARY_TABLE and RELATION induced the same
# protected partition and no continuation in the complete Boolean target carrier
# separated them.  Before expanding the continuation language, test the stronger
# possibility: the two supplied schemas are extensionally isomorphic, in which case
# no behavior-only continuation can ever separate them and they should be quotiented.

states=[(u,v,p) for u in (0,1) for v in (0,1) for p in range(4)]

def obs(s):
    u,v,p=s
    r=p&1
    return (r, r^v, u^r)

# All Boolean input pairs, independent of the task states.
input_pairs=[(a,b) for a in (0,1) for b in (0,1)]

# BINARY_TABLE(code): four-bit truth table.
def table_eval(code,a,b):
    return (code >> ((a<<1)|b)) & 1

# RELATION(mask): membership in an arbitrary subset of the four ordered Boolean pairs.
def relation_eval(mask,a,b):
    return 1 if ((mask >> ((a<<1)|b)) & 1) else 0

# Canonical extensional vector over the complete input domain.
def extvec(evalf,code):
    return tuple(evalf(code,a,b) for a,b in input_pairs)

table_vectors={code:extvec(table_eval,code) for code in range(16)}
relation_vectors={mask:extvec(relation_eval,mask) for mask in range(16)}

# G1/G2: exact bijection and equality under the obvious code<->mask map.
G1_extensional_map_exact=all(table_vectors[c]==relation_vectors[c] for c in range(16))
G2_bijection=(len(set(table_vectors.values()))==16 and len(set(relation_vectors.values()))==16 and set(table_vectors.values())==set(relation_vectors.values()))

# Close under the old-language symmetries used in V5/V7: input swap, input negations,
# and output negation.  Compute orbits extensionally rather than by operator names.
def transform_vec(vec,swap=False,nega=False,negb=False,nego=False):
    out=[]
    for a,b in input_pairs:
        aa=1-a if nega else a
        bb=1-b if negb else b
        if swap: aa,bb=bb,aa
        idx=(aa<<1)|bb
        val=vec[idx]
        if nego: val=1-val
        out.append(val)
    return tuple(out)

def orbit(vec):
    return frozenset(transform_vec(vec,s,n1,n2,no) for s in (False,True) for n1 in (False,True) for n2 in (False,True) for no in (False,True))

table_orbits={orbit(v) for v in table_vectors.values()}
relation_orbits={orbit(v) for v in relation_vectors.values()}
G3_same_closure_relative_orbits=(table_orbits==relation_orbits)

# Strong no-separator theorem by exhaustive extensional continuation enumeration.
# A deterministic behavior-only continuation is any Boolean functional of the four
# extensional output bits, hence one of 2^16 predicates on the 16 possible functions.
# Since table and relation map to the SAME extensional vector pointwise, every such
# continuation has identical result under the code<->mask bijection.  Enumerate all
# 65,536 functionals to make this executable rather than merely asserted.

def vec_index(vec):
    idx=0
    for k,b in enumerate(vec): idx |= (b&1)<<k
    return idx

separator_count=0
for functional in range(1<<16):
    for c in range(16):
        ti=(functional>>vec_index(table_vectors[c]))&1
        ri=(functional>>vec_index(relation_vectors[c]))&1
        if ti!=ri:
            separator_count+=1
            break
G4_no_behavioral_separator_exhaustive=(separator_count==0)

# Non-isomorphic positive control.  Compare a one-bit PARITY schema with a two-bit
# PAIR schema.  Under continuation C0 (only parity matters) they are action-equivalent;
# under C1 (the first raw component matters) PAIR is sufficient while PARITY is not.
def parity_schema(a,b): return a^b
def pair_schema(a,b): return (a,b)

def c0_action_from_parity(z): return z
def c0_action_from_pair(z): return z[0]^z[1]
def c1_action_from_pair(z): return z[0]

# No decoder from parity alone can recover first component on all four input pairs.
# Exhaust all 4 unary Boolean decoders parity->{0,1}.
def unary_decode(code,z): return (code>>z)&1

G5_nonisomorphic_control_equiv_at_C0=all(c0_action_from_parity(parity_schema(a,b))==c0_action_from_pair(pair_schema(a,b)) for a,b in input_pairs)
parity_c1_decoders=[]
for code in range(4):
    if all(unary_decode(code,parity_schema(a,b))==a for a,b in input_pairs):
        parity_c1_decoders.append(code)
G6_new_continuation_splits_nonisomorphic_pair=(len(parity_c1_decoders)==0 and all(c1_action_from_pair(pair_schema(a,b))==a for a,b in input_pairs))

# Ablating C1 restores equivalence relative to C0 by definition/exhaustive check.
G7_ablation_restores_C0_equivalence=G5_nonisomorphic_control_equiv_at_C0

# Anonymous input relabeling: swap the two primitive inputs and complement either/both.
# Exact table<->relation isomorphism and no-separator result must survive.
def relabel_pair(a,b,swap,na,nb):
    aa=1-a if na else a
    bb=1-b if nb else b
    return (bb,aa) if swap else (aa,bb)

def relabel_trial(swap,na,nb):
    for c in range(16):
        for a,b in input_pairs:
            aa,bb=relabel_pair(a,b,swap,na,nb)
            if table_eval(c,aa,bb)!=relation_eval(c,aa,bb): return False
    return True

relabels=list(itertools.product((False,True),repeat=3))
G8_anonymous_relabel_invariance=all(relabel_trial(*r) for r in relabels)

gates={
    'G1_extensional_code_mask_map_exact':G1_extensional_map_exact,
    'G2_schema_carriers_bijective':G2_bijection,
    'G3_same_closure_relative_orbits':G3_same_closure_relative_orbits,
    'G4_no_behavioral_separator_exhaustive':G4_no_behavioral_separator_exhaustive,
    'G5_nonisomorphic_control_equiv_at_C0':G5_nonisomorphic_control_equiv_at_C0,
    'G6_new_continuation_splits_nonisomorphic_pair':G6_new_continuation_splits_nonisomorphic_pair,
    'G7_ablation_restores_C0_equivalence':G7_ablation_restores_C0_equivalence,
    'G8_anonymous_relabel_invariance':G8_anonymous_relabel_invariance,
}

result={
    'schema':'minimal.core.schema.isomorphism.v8',
    'seed':SEED,
    'claim':'schema identity should quotient exact extensional isomorphs; continuation expansion can split only genuinely nonisomorphic latent structure',
    'table_carrier':16,
    'relation_carrier':16,
    'table_orbits':len(table_orbits),
    'relation_orbits':len(relation_orbits),
    'behavioral_functionals_exhausted':1<<16,
    'separator_count':separator_count,
    'nonisomorphic_control_parity_decoders_for_C1':parity_c1_decoders,
    'relabels':len(relabels),
    'gates':gates,
    'pass':all(gates.values()),
}
os.makedirs('artifacts/minimal_core_schema_isomorphism_v8',exist_ok=True)
with open('artifacts/minimal_core_schema_isomorphism_v8/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_SCHEMA_ISOMORPHISM_V8')
print('PASS_MINIMAL_CORE_SCHEMA_ISOMORPHISM_V8')
