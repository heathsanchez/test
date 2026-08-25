import itertools, json, os

SEED=2026082603

# Four-state latent domain; representations are partitions of {0,1,2,3}.
states=tuple(range(4))

# Candidate continuations are all 16 Boolean predicates on the four states.
def pred(code,s): return (code>>s)&1

# A representation partition is sufficient for a predicate iff the predicate is constant on every block.
def sufficient(partition, code):
    for block in partition:
        vals={pred(code,s) for s in block}
        if len(vals)>1: return False
    return True

# Mixed pool: four permanent (identical partitions under relabelled presentation) and four provisional compressed-vs-rich.
# Every pair is equivalent for C0=constant-0 (code 0).
pairs=[]
# Permanent pairs
perms=[(0,1,2,3),(1,0,3,2),(2,3,0,1),(3,2,1,0)]
base_parts=[((0,1),(2,3)), ((0,2),(1,3)), ((0,3),(1,2)), ((0,),(1,2,3))]
for i,(part,pm) in enumerate(zip(base_parts,perms)):
    # same extensional partition, merely block/order presentation changed
    A=tuple(tuple(block) for block in part)
    B=tuple(reversed(tuple(reversed(block)) for block in part))
    pairs.append((f'P{i}',A,B,True))

# Provisional pairs: coarse vs strict refinement.
prov=[
    (((0,1),(2,3)),((0,),(1,),(2,3))),
    (((0,2),(1,3)),((0,),(2,),(1,3))),
    (((0,3),(1,2)),((0,),(3,),(1,2))),
    (((0,1,2),(3,)),((0,1),(2,),(3,))),
]
for j,(A,B) in enumerate(prov,4):
    pairs.append((f'P{j}',A,B,False))

C0=0
G1_all_equiv_C0=all(sufficient(A,C0)==sufficient(B,C0) for _,A,B,_ in pairs)

# Ground truth from exhaustive carrier, but controller is not allowed to use it directly.
all_codes=list(range(16))
ground={}
for pid,A,B,perm in pairs:
    seps=[c for c in all_codes if sufficient(A,c)!=sufficient(B,c)]
    ground[pid]={'permanent':len(seps)==0,'separators':seps}

# Active policy: choose next continuation that maximizes expected distinction gain across unresolved pairs,
# penalized by predicate complexity. It sees only current partition structures and previously returned verifier outcomes.
def complexity(code):
    ones=bin(code).count('1')
    return min(ones,4-ones)

queried=[]
unresolved={pid for pid,_,_,_ in pairs}
status={pid:'UNRESOLVED' for pid in unresolved}
history=[]

# Map ids to partitions
pmap={pid:(A,B) for pid,A,B,_ in pairs}

while unresolved:
    remaining=[c for c in all_codes if c not in queried]
    if not remaining: break
    scored=[]
    for c in remaining:
        # predicted informative count is computable from the candidate representations themselves;
        # it does not peek at ground labels.
        informative=sum(1 for pid in unresolved if sufficient(pmap[pid][0],c)!=sufficient(pmap[pid][1],c))
        # Prefer more splits; then simpler predicates; then code.
        scored.append((-informative, complexity(c), c))
    scored.sort()
    _,_,q=scored[0]
    queried.append(q)
    split_now=[]
    for pid in list(unresolved):
        A,B=pmap[pid]
        outcome=(sufficient(A,q)!=sufficient(B,q))
        if outcome:
            status[pid]='PROVISIONAL_SPLIT'
            unresolved.remove(pid)
            split_now.append(pid)
    history.append({'query':q,'split':sorted(split_now),'remaining':sorted(unresolved)})
    # Stop if no remaining candidate can possibly distinguish any unresolved pair.
    if unresolved:
        max_future=max(sum(1 for pid in unresolved if sufficient(pmap[pid][0],c)!=sufficient(pmap[pid][1],c)) for c in all_codes if c not in queried) if len(queried)<16 else 0
        if max_future==0:
            break

# IMPORTANT: zero-separator / permanence still requires CompleteCover over the residual continuation carrier.
# We do not infer permanence from active search alone. We certify remaining pairs by exhaustive no-separator check.
certified_codes=set(queried)
for pid in list(unresolved):
    A,B=pmap[pid]
    rest=[c for c in all_codes if c not in certified_codes]
    sep=[c for c in rest if sufficient(A,c)!=sufficient(B,c)]
    if not sep:
        status[pid]='PERMANENT_AFTER_COMPLETECOVER'
        unresolved.remove(pid)

G2_active_finds_all_provisional=all(status[pid]=='PROVISIONAL_SPLIT' for pid,_,_,perm in pairs if not perm)
G3_no_false_split_permanent=all(status[pid]!='PROVISIONAL_SPLIT' for pid,_,_,perm in pairs if perm)
G4_permanence_only_after_completecover=all(status[pid]=='PERMANENT_AFTER_COMPLETECOVER' for pid,_,_,perm in pairs if perm)
G5_classification_exact=all((status[pid]=='PERMANENT_AFTER_COMPLETECOVER')==perm for pid,_,_,perm in pairs)

# Efficiency: active separator discovery should use fewer than all 16 continuations before all provisional pairs split.
# Count queries through the step when the last provisional split occurred.
last_split_step=0
seen=set()
for i,h in enumerate(history,1):
    seen.update(h['split'])
    if all(f'P{k}' in seen for k in range(4,8)):
        last_split_step=i; break
G6_strict_discovery_compression=(last_split_step>0 and last_split_step<16)

# Negative control: lexical/code-order policy should not be credited as targeted search; compare queries to split all provisional pairs.
def steps_policy(order):
    openp={f'P{k}' for k in range(4,8)}
    n=0
    for c in order:
        n+=1
        for pid in list(openp):
            A,B=pmap[pid]
            if sufficient(A,c)!=sufficient(B,c): openp.remove(pid)
        if not openp: return n
    return 16
lex_steps=steps_policy(list(range(16)))
G7_active_not_worse_than_lex=(last_split_step<=lex_steps)

# Relabel invariance across all 24 state permutations.
def relabel_partition(part,pm):
    return tuple(tuple(sorted(pm[s] for s in block)) for block in part)

def remap_code(code,pm):
    # q'(pm[s]) = q(s)
    out=0
    for s in states:
        if pred(code,s): out |= (1<<pm[s])
    return out

def active_steps_for(relabel):
    rp={pid:(relabel_partition(A,relabel),relabel_partition(B,relabel)) for pid,A,B,_ in pairs}
    unresolved={f'P{k}' for k in range(4,8)}
    used=[]
    for _ in range(16):
        remaining=[c for c in all_codes if c not in used]
        scored=[]
        for c in remaining:
            inf=sum(1 for pid in unresolved if sufficient(rp[pid][0],c)!=sufficient(rp[pid][1],c))
            scored.append((-inf,complexity(c),c))
        scored.sort(); q=scored[0][2]; used.append(q)
        for pid in list(unresolved):
            if sufficient(rp[pid][0],q)!=sufficient(rp[pid][1],q): unresolved.remove(pid)
        if not unresolved: return len(used)
    return 16

perm_steps=[active_steps_for(pm) for pm in itertools.permutations(states)]
G8_relabel_invariance=all(x<16 for x in perm_steps)

gates={
 'G1_all_pairs_equivalent_at_C0':G1_all_equiv_C0,
 'G2_active_search_finds_all_provisional':G2_active_finds_all_provisional,
 'G3_no_false_split_of_permanent':G3_no_false_split_permanent,
 'G4_permanence_requires_completecover':G4_permanence_only_after_completecover,
 'G5_final_classification_exact':G5_classification_exact,
 'G6_separator_discovery_strictly_below_full_enumeration':G6_strict_discovery_compression,
 'G7_active_policy_not_worse_than_lexical_control':G7_active_not_worse_than_lex,
 'G8_anonymous_relabel_invariance':G8_relabel_invariance,
}

result={
 'schema':'minimal.core.active.separator.search.v10',
 'seed':SEED,
 'claim':'adaptive search can prioritize distinction-changing continuations while permanence remains CompleteCover-relative',
 'active_queries':queried,
 'active_steps_to_split_all_provisional':last_split_step,
 'lexical_steps_to_split_all_provisional':lex_steps,
 'full_carrier_size':16,
 'history':history,
 'status':status,
 'relabel_steps_min':min(perm_steps),
 'relabel_steps_max':max(perm_steps),
 'gates':gates,
 'pass':all(gates.values())
}
os.makedirs('artifacts/minimal_core_active_separator_search_v10',exist_ok=True)
with open('artifacts/minimal_core_active_separator_search_v10/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_ACTIVE_SEPARATOR_SEARCH_V10')
print('PASS_MINIMAL_CORE_ACTIVE_SEPARATOR_SEARCH_V10')
