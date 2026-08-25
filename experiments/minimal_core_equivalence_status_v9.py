import itertools, json, os, random

SEED=2026082602
rng=random.Random(SEED)

# Finite latent domain of four states.
states=[(a,b) for a in (0,1) for b in (0,1)]

# Representation key functions.
def k_id(s):
    a,b=s; return (a,b)
def k_id_code(s):
    a,b=s; return 2*a+b

def k_parity(s):
    a,b=s; return a^b
def k_nparity(s):
    return 1-k_parity(s)

def k_a(s): return s[0]
def k_na(s): return 1-s[0]

def k_or(s):
    a,b=s; return a|b
def k_or_rel(s):
    a,b=s; return int((a,b) in {(0,1),(1,0),(1,1)})

def k_and(s):
    a,b=s; return a&b

def k_eq(s):
    a,b=s; return int(a==b)

# Mixed pool. Names are used only for reporting; classification uses behavior only.
# Four exact-partition isomorph pairs and four merely C0-equivalent compressed-vs-rich pairs.
pairs=[
    {"id":"P0","left":k_id,"right":k_id_code,"c0":lambda s: 0},
    {"id":"P1","left":k_parity,"right":k_nparity,"c0":k_parity},
    {"id":"P2","left":k_a,"right":k_na,"c0":k_a},
    {"id":"P3","left":k_or,"right":k_or_rel,"c0":k_or},
    {"id":"P4","left":k_parity,"right":k_id,"c0":k_parity},
    {"id":"P5","left":k_a,"right":k_id,"c0":k_a},
    {"id":"P6","left":k_or,"right":k_id,"c0":k_or},
    {"id":"P7","left":k_eq,"right":k_id,"c0":k_eq},
]
rng.shuffle(pairs)

# Canonical partition induced by a representation.
def part_sig(keyf, xs=states):
    groups={}
    for i,s in enumerate(xs): groups.setdefault(keyf(s),[]).append(i)
    return tuple(sorted(tuple(v) for v in groups.values()))

def sufficient(keyf,target):
    groups={}
    for s in states: groups.setdefault(keyf(s),[]).append(s)
    for block in groups.values():
        if len({target(s) for s in block})>1:
            return False
    return True

# Full declared future continuation carrier = all 16 Boolean predicates on the 4 latent states.
def target_from_code(code):
    bits=[(code>>i)&1 for i in range(4)]
    return lambda s,bits=bits: bits[states.index(s)]

carrier=[(code,target_from_code(code)) for code in range(16)]
# complexity order is precommitted: constant functions first, then min support size, then code.
def complexity(code):
    ones=bin(code).count('1')
    return (min(ones,4-ones), code)
carrier_ordered=sorted(carrier,key=lambda x:complexity(x[0]))

records=[]
for p in pairs:
    lp=part_sig(p['left']); rp=part_sig(p['right'])
    ground_permanent=(lp==rp)  # exact extensional/partition identity in this bounded world
    c0_left=sufficient(p['left'],p['c0'])
    c0_right=sufficient(p['right'],p['c0'])
    c0_equiv=(c0_left==c0_right==True)

    separators=[]
    for code,t in carrier_ordered:
        sl=sufficient(p['left'],t); sr=sufficient(p['right'],t)
        if sl!=sr: separators.append((complexity(code),code,sl,sr))

    first_sep=separators[0] if separators else None
    # Evidence-driven status law: never call permanent before CompleteCover.
    # Provisional is certified as soon as a separator appears; permanent only after full carrier exhaustion with zero separators.
    inferred='PROVISIONAL' if first_sep else 'PERMANENT'
    records.append({
        'id':p['id'],
        'ground_permanent':ground_permanent,
        'c0_equivalent':c0_equiv,
        'separator_count':len(separators),
        'first_separator_code':(first_sep[1] if first_sep else None),
        'first_separator_complexity':(first_sep[0] if first_sep else None),
        'inferred':inferred,
        'correct': inferred == ('PERMANENT' if ground_permanent else 'PROVISIONAL'),
    })

# Premature-permanence separator: before full cover, at least one provisional pair must still look unsplit after a strict prefix.
prefix_codes=[code for code,_ in carrier_ordered[:3]]
premature_ambiguous=[]
for p in pairs:
    if part_sig(p['left'])==part_sig(p['right']):
        continue
    split=False
    for code in prefix_codes:
        t=target_from_code(code)
        if sufficient(p['left'],t)!=sufficient(p['right'],t): split=True
    if not split: premature_ambiguous.append(p['id'])

# Progressive update trace: all pairs start CURRENT_EQUIVALENT under their local C0.
# As full carrier evidence arrives, only provisional pairs split; permanent pairs never do.
progress=[]
status={p['id']:'UNRESOLVED_EQUIVALENT' for p in pairs}
for code,t in carrier_ordered:
    newly=[]
    for p in pairs:
        if status[p['id']]!='UNRESOLVED_EQUIVALENT':
            continue
        if sufficient(p['left'],t)!=sufficient(p['right'],t):
            status[p['id']]='PROVISIONAL_SPLIT'
            newly.append(p['id'])
    progress.append({'code':code,'newly_split':sorted(newly)})
for p in pairs:
    if status[p['id']]=='UNRESOLVED_EQUIVALENT': status[p['id']]='PERMANENT_AFTER_COMPLETECOVER'

# Anonymous state relabel invariance: permuting latent state indices changes truth-table codes but not classification.
def relabel_trial(perm):
    rs=[states[i] for i in perm]
    def psig(keyf):
        groups={}
        for i,s in enumerate(rs): groups.setdefault(keyf(s),[]).append(i)
        return tuple(sorted(tuple(v) for v in groups.values()))
    def suff(keyf,bits):
        groups={}
        for i,s in enumerate(rs): groups.setdefault(keyf(s),[]).append(i)
        for inds in groups.values():
            if len({bits[i] for i in inds})>1: return False
        return True
    for p in pairs:
        gp=(psig(p['left'])==psig(p['right']))
        sep=False
        for code in range(16):
            bits=[(code>>i)&1 for i in range(4)]
            if suff(p['left'],bits)!=suff(p['right'],bits): sep=True; break
        inferred_perm=not sep
        if inferred_perm!=gp: return False
    return True

perms=list(itertools.permutations(range(4)))
relabel_ok=all(relabel_trial(pm) for pm in perms)

permanent=[r for r in records if r['ground_permanent']]
provisional=[r for r in records if not r['ground_permanent']]

gates={
    'G1_all_pairs_equivalent_at_C0': all(r['c0_equivalent'] for r in records),
    'G2_mixed_pool_contains_both_statuses': bool(permanent and provisional),
    'G3_all_true_permanent_have_zero_separators': all(r['separator_count']==0 for r in permanent),
    'G4_all_true_provisional_eventually_split': all(r['separator_count']>0 for r in provisional),
    'G5_evidence_rule_classifies_all_pairs_exactly': all(r['correct'] for r in records),
    'G6_no_permanent_pair_splits_during_growth': all(status[r['id']]=='PERMANENT_AFTER_COMPLETECOVER' for r in permanent),
    'G7_every_provisional_pair_is_selectively_revised': all(status[r['id']]=='PROVISIONAL_SPLIT' for r in provisional),
    'G8_premature_permanence_is_not_licensed': len(premature_ambiguous)>0,
    'G9_complete_carrier_exhausted': len(carrier)==16,
    'G10_anonymous_state_relabel_invariance': relabel_ok,
}

result={
    'schema':'minimal.core.equivalence.status.v9',
    'seed':SEED,
    'claim':'permanent quotient requires CompleteCover no-separator evidence; provisional quotient is revoked/refined by a separating future continuation',
    'pair_count':len(records),
    'permanent_count':len(permanent),
    'provisional_count':len(provisional),
    'continuation_carrier_size':len(carrier),
    'premature_ambiguous_pairs':sorted(premature_ambiguous),
    'records':records,
    'final_status':status,
    'state_relabels':len(perms),
    'gates':gates,
    'pass':all(gates.values()),
}

os.makedirs('artifacts/minimal_core_equivalence_status_v9',exist_ok=True)
with open('artifacts/minimal_core_equivalence_status_v9/result.json','w') as f: json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps(result,indent=2,sort_keys=True))
if not result['pass']: raise SystemExit('FAIL_MINIMAL_CORE_EQUIVALENCE_STATUS_V9')
print('PASS_MINIMAL_CORE_EQUIVALENCE_STATUS_V9')
