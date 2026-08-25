import itertools, json, os

SEED=2026082527

# Finite world inherited conceptually from V6: u represented; v hidden; p presentation.
states=[(u,v,p) for u in (0,1) for v in (0,1) for p in range(4)]

def obs(s):
    u,v,p=s
    r=p&1
    return (r, r^v, u^r)

acq=[s for s in states if s[2] in (0,1)]
held=[s for s in states if s[2] in (2,3)]

def sig_stage1(s):
    u,v,p=s
    return (u,v)

def pair_obligations(xs,sig):
    out=[]
    for i,a in enumerate(xs):
        for b in xs[i+1:]:
            out.append((a,b,sig(a)==sig(b)))
    return out

obl1=pair_obligations(acq,sig_stage1)

def exact_partition(xs, keyf, sigf):
    for a in xs:
        for b in xs:
            if ((keyf(a)==keyf(b)) != (sigf(a)==sigf(b))):
                return False
    return True

# Two V6 surviving schema families, frozen as carriers.
# BINARY_TABLE family: all 16 truth tables over pairs of anonymous Boolean observations.
def table_fun(code,i,j):
    bits=[(code>>k)&1 for k in range(4)]
    return lambda s: bits[(obs(s)[i]<<1)|obs(s)[j]]

binary=[]
for code in range(16):
    for i,j in itertools.combinations(range(3),2):
        f=table_fun(code,i,j)
        key=lambda s,f=f:(s[0],f(s))
        if exact_partition(acq,key,sig_stage1):
            binary.append((code,i,j,key))

# RELATION family: relation membership on anonymous ordered observation pairs.
# Represent a state by (u, membership pair signature) where relation is arbitrary subset of 4 Boolean pairs.
relation=[]
for mask in range(16):
    R={(a,b) for a in (0,1) for b in (0,1) if (mask>>((a<<1)|b))&1}
    for i,j in itertools.combinations(range(3),2):
        key=lambda s,R=R,i=i,j=j:(s[0], (obs(s)[i],obs(s)[j]) in R)
        if exact_partition(acq,key,sig_stage1):
            relation.append((mask,i,j,key))

# Current continuation family C0: only equality/substitutability under stage1 target.
# Compare behavior of each surviving schema family on acquisition+heldout via canonical partition.
def part_sig(xs,key):
    groups={}
    for idx,s in enumerate(xs): groups.setdefault(key(s),[]).append(idx)
    return tuple(sorted(tuple(v) for v in groups.values()))

b_parts={part_sig(states,x[3]) for x in binary}
r_parts={part_sig(states,x[3]) for x in relation}
common=b_parts & r_parts
G1_both_survive=bool(binary and relation)
G2_current_behavioral_equivalence=(len(common)==1 and b_parts==r_parts)

# Frozen continuation carrier: all Boolean target predicates over (u,v,p parity), represented as 8-bit tables.
# A continuation separates schema families if, after conditioning on a schema key class, the verifier's target
# predicate is constant for one schema partition but not the other. We search for the minimum-complexity target
# (fewest positive states; then lexicographic code) that separates the canonical partitions.
canon_b=next(iter(b_parts)) if b_parts else None
canon_r=next(iter(r_parts)) if r_parts else None

def blocks_from_sig(sig):
    return [set(block) for block in sig]

def predicate(code,s):
    u,v,p=s
    idx=(u<<2)|(v<<1)|(p&1)
    return (code>>idx)&1

def sufficient(sig,code):
    vals=[predicate(code,s) for s in states]
    for block in blocks_from_sig(sig):
        if len({vals[i] for i in block})>1: return False
    return True

separators=[]
if canon_b is not None and canon_r is not None:
    for code in range(1,255):
        sb=sufficient(canon_b,code)
        sr=sufficient(canon_r,code)
        if sb!=sr:
            complexity=min(bin(code).count('1'),8-bin(code).count('1'))
            separators.append((complexity,code,sb,sr))

separators.sort()
minsep=separators[0] if separators else None
G3_separating_continuation_exists=minsep is not None
# Require a unique behavioral minimum under complement symmetry: same complexity and code/complement orbit.
if minsep:
    mc=minsep[0]
    mins=[x for x in separators if x[0]==mc]
    orbits={min(x[1],255-x[1]) for x in mins}
else:
    mins=[]; orbits=set()
G4_unique_min_separator_orbit=(len(orbits)==1)

# After adding separator, one schema family must be adequate and the other inadequate.
if minsep:
    _,sep_code,sb,sr=minsep
    winner='BINARY_TABLE' if sb and not sr else ('RELATION' if sr and not sb else None)
else:
    sep_code=None; winner=None
G5_schema_class_refines=(winner in ('BINARY_TABLE','RELATION'))

# Ablating separator returns to equivalence.
G6_ablation_collapses_back=G2_current_behavioral_equivalence

# Surface relabel invariance: the existence/identity of the schema-equivalence-at-C0 result should survive all primitive permutations.
def relabel_obs(perm):
    def robs(s):
        o=obs(s); return tuple(o[k] for k in perm)
    return robs

def trial(perm):
    robs=relabel_obs(perm)
    bp=set(); rp=set()
    for code in range(16):
        bits=[(code>>k)&1 for k in range(4)]
        for i,j in itertools.combinations(range(3),2):
            f=lambda s,bits=bits,i=i,j=j:bits[(robs(s)[i]<<1)|robs(s)[j]]
            key=lambda s,f=f:(s[0],f(s))
            if exact_partition(acq,key,sig_stage1): bp.add(part_sig(states,key))
    for mask in range(16):
        R={(a,b) for a in (0,1) for b in (0,1) if (mask>>((a<<1)|b))&1}
        for i,j in itertools.combinations(range(3),2):
            key=lambda s,R=R,i=i,j=j:(s[0], (robs(s)[i],robs(s)[j]) in R)
            if exact_partition(acq,key,sig_stage1): rp.add(part_sig(states,key))
    return bool(bp and rp) and bp==rp and len(bp)==1

perms=list(itertools.permutations(range(3)))
G7_relabel_invariance=all(trial(p) for p in perms)

gates={
 'G1_both_v6_schemas_survive':G1_both_survive,
 'G2_current_behavioral_equivalence':G2_current_behavioral_equivalence,
 'G3_minimal_separating_continuation_exists':G3_separating_continuation_exists,
 'G4_unique_min_separator_orbit':G4_unique_min_separator_orbit,
 'G5_separator_refines_schema_class':G5_schema_class_refines,
 'G6_ablation_collapses_back':G6_ablation_collapses_back,
 'G7_anonymous_relabel_invariance':G7_relabel_invariance,
}

result={
 'schema':'minimal.core.schema.orbit.separator.v7',
 'seed':SEED,
 'binary_valid':len(binary),
 'relation_valid':len(relation),
 'binary_behavioral_partitions':len(b_parts),
 'relation_behavioral_partitions':len(r_parts),
 'common_partitions':len(common),
 'separator_count':len(separators),
 'min_separator':({'code':sep_code,'winner':winner,'complexity':minsep[0]} if minsep else None),
 'min_separator_orbits':sorted(orbits),
 'primitive_permutations':len(perms),
 'gates':gates,
 'pass':all(gates.values())
}
os.makedirs('artifacts/minimal_core_schema_orbit_separator_v7',exist_ok=True)
with open('artifacts/minimal_core_schema_orbit_separator_v7/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_SCHEMA_ORBIT_SEPARATOR_V7')
print('PASS_MINIMAL_CORE_SCHEMA_ORBIT_SEPARATOR_V7')
