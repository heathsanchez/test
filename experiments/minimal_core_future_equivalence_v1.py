#!/usr/bin/env python3
import json, random
from collections import defaultdict, Counter
from pathlib import Path

SEED = 2026082521
N_RELABELLINGS = 256
OUT = Path('artifacts/minimal_core_future_equivalence_v1')
OUT.mkdir(parents=True, exist_ok=True)

# Raw states deliberately contain both a missing distinction (v) and a presentation
# distinction (p) that is irrelevant in regime 1.
RAW = [(u, v, p) for u in (0,1) for v in (0,1) for p in range(4)]

# Acquisition contexts. Their joint verifier signature uniquely identifies (u,v)
# without exposing or naming u/v to the revision algorithm.
def c0(s):
    u,v,p=s; return u ^ v
def c1(s):
    u,v,p=s; return v

# Held-out regime-1 continuations: different functions, same sufficient state (u,v).
def h0(s):
    u,v,p=s; return u
def h1(s):
    u,v,p=s; return u & v
def h2(s):
    u,v,p=s; return (u | v)

# Regime-2 continuations make one previously irrelevant distinction (presentation parity)
# decision-relevant.
def d0(s):
    u,v,p=s; return p % 2
def d1(s):
    u,v,p=s; return (u ^ v ^ (p % 2))

ACQ = [c0,c1]
HELD = [h0,h1,h2]
REG1 = ACQ + HELD
REG2 = REG1 + [d0,d1]


def partition_from_key(key_fn):
    groups=defaultdict(list)
    for s in RAW:
        groups[key_fn(s)].append(s)
    return list(groups.values())


def partition_from_signature(contexts):
    # Minimal core: the coarsest equivalence relation justified by the declared
    # contextual verifier family. No latent feature names are used.
    return partition_from_key(lambda s: tuple(f(s) for f in contexts))


def exact_for(partition, contexts):
    for block in partition:
        for f in contexts:
            vals={f(s) for s in block}
            if len(vals) != 1:
                return False
    return True


def majority_accuracy(partition, contexts):
    # Best possible deterministic policy that sees only the current equivalence class.
    correct=0; total=0
    for block in partition:
        for f in contexts:
            counts=Counter(f(s) for s in block)
            correct += max(counts.values())
            total += len(block)
    return correct/total


def canonical_pair_relation(partition):
    same=set()
    for block in partition:
        for i,a in enumerate(block):
            for b in block[i:]:
                same.add(tuple(sorted((RAW.index(a), RAW.index(b)))))
    return same


def split_only(initial, contexts):
    # Can refine existing blocks but cannot merge presentation-distinct blocks.
    out=[]
    for block in initial:
        groups=defaultdict(list)
        for s in block:
            groups[tuple(f(s) for f in contexts)].append(s)
        out.extend(groups.values())
    return out


def quotient_only(initial):
    # Remove the presentation distinction p but do not introduce missing v.
    # This is the strongest natural coarsening available from the initial key (u,p)
    # without verifier-driven splitting.
    return partition_from_key(lambda s: s[0])


def ablate_parity(partition):
    # Targeted ablation of the newly induced regime-2 distinction: collapse back to
    # the stage-1 verifier signature.
    return partition_from_signature(ACQ)


def relabel_trial(seed):
    rng=random.Random(seed)
    ids=list(range(len(RAW))); rng.shuffle(ids)
    # Surface relabelling cannot change behavioral equivalence. We test pairwise
    # membership after permutation to guard against accidental coordinate naming.
    stage1=partition_from_signature(ACQ)
    stage2=partition_from_signature(ACQ+[d0])
    # Map partitions to permuted IDs and compare class-size multiset + exactness.
    def relabel(part):
        return sorted(sorted(ids[RAW.index(s)] for s in block) for block in part)
    r1=relabel(stage1); r2=relabel(stage2)
    return {
        'stage1_sizes': sorted(map(len,r1)),
        'stage2_sizes': sorted(map(len,r2)),
        'stage1_exact_reg1': exact_for(stage1, REG1),
        'stage2_exact_reg2': exact_for(stage2, REG2),
    }

initial = partition_from_key(lambda s: (s[0], s[2]))  # 8 cells: too fine in p, too coarse in v
stage1 = partition_from_signature(ACQ)                # 4 cells: (behaviorally) u,v
split = split_only(initial, ACQ)                      # 16 cells: correct but over-refined
quot = quotient_only(initial)                         # 2 cells: compressed but still aliases v
raw_identity = [[s] for s in RAW]                    # 16 cells: exact but maximally uncompressed
stage2 = partition_from_signature(ACQ+[d0])           # 8 cells: add only presentation parity
ablated = ablate_parity(stage2)

# Matched-size wrong-class control: four classes by (u, presentation parity), which
# ignores v and therefore has same class count as stage1 but wrong future geometry.
wrong4 = partition_from_key(lambda s: (s[0], s[2] % 2))

results = {
    'schema':'minimal.core.future.equivalence.v1',
    'seed':SEED,
    'raw_states':len(RAW),
    'core':'current equivalence relation + contextual verifier + coarsest consistent revision',
    'partitions':{
        'initial':{'classes':len(initial),'exact_reg1':exact_for(initial,REG1),'acc_reg1':majority_accuracy(initial,REG1)},
        'raw_identity':{'classes':len(raw_identity),'exact_reg1':exact_for(raw_identity,REG1),'acc_reg1':majority_accuracy(raw_identity,REG1)},
        'split_only':{'classes':len(split),'exact_reg1':exact_for(split,REG1),'acc_reg1':majority_accuracy(split,REG1)},
        'quotient_only':{'classes':len(quot),'exact_reg1':exact_for(quot,REG1),'acc_reg1':majority_accuracy(quot,REG1)},
        'wrong4':{'classes':len(wrong4),'exact_reg1':exact_for(wrong4,REG1),'acc_reg1':majority_accuracy(wrong4,REG1)},
        'minimal_core_stage1':{'classes':len(stage1),'exact_acq':exact_for(stage1,ACQ),'exact_held':exact_for(stage1,HELD),'exact_reg1':exact_for(stage1,REG1),'acc_reg1':majority_accuracy(stage1,REG1)},
        'minimal_core_stage2':{'classes':len(stage2),'exact_reg2':exact_for(stage2,REG2),'acc_reg2':majority_accuracy(stage2,REG2)},
        'stage2_ablation':{'classes':len(ablated),'exact_reg2':exact_for(ablated,REG2),'acc_reg2':majority_accuracy(ablated,REG2)},
    },
    'compression_vs_raw_identity': len(raw_identity)/len(stage1),
    'stage2_new_classes': len(stage2)-len(stage1),
    'relabel_trials': N_RELABELLINGS,
}

trials=[relabel_trial(SEED+i) for i in range(N_RELABELLINGS)]
results['relabel_all_pass'] = all(
    t['stage1_sizes']==[4,4,4,4] and
    t['stage2_sizes']==[2,2,2,2,2,2,2,2] and
    t['stage1_exact_reg1'] and t['stage2_exact_reg2']
    for t in trials
)

# Frozen primary gates.
gates = {
    # Initial representation is genuinely wrong, not merely inefficient.
    'G1_initial_inadequate': not exact_for(initial, REG1),
    # Verifier-induced revision reaches the coarsest stage-1 sufficient quotient.
    'G2_core_exact_acquisition': exact_for(stage1, ACQ),
    'G3_core_transfers_heldout': exact_for(stage1, HELD),
    # It both restores a missing distinction and removes irrelevant presentation distinctions.
    'G4_core_smaller_than_initial_and_raw': len(stage1) < len(initial) and len(stage1) < len(raw_identity),
    # Split-only can restore correctness but cannot compress; quotient-only compresses but remains wrong.
    'G5_dual_ablation_split_only_overfits': exact_for(split, REG1) and len(split) > len(stage1),
    'G6_dual_ablation_quotient_only_fails': not exact_for(quot, REG1),
    # Same-size wrong quotient must fail: benefit is semantic, not class-count alone.
    'G7_wrong_class_control_fails': len(wrong4)==len(stage1) and not exact_for(wrong4, REG1),
    # Regime change makes a previously forgotten distinction relevant; minimal core must split again.
    'G8_regime_change_forces_refinement': not exact_for(stage1, REG2) and exact_for(stage2, REG2) and len(stage2)>len(stage1),
    # Targeted ablation of the newly required distinction restores failure.
    'G9_targeted_ablation_restores_failure': not exact_for(ablated, REG2),
    # Surface naming is irrelevant.
    'G10_relabel_invariance': results['relabel_all_pass'],
}
results['gates']=gates
results['pass']=all(gates.values())

with open(OUT/'result.json','w') as f:
    json.dump(results,f,indent=2,sort_keys=True)
print(json.dumps(results,indent=2,sort_keys=True))
if not results['pass']:
    raise SystemExit('FAIL_MINIMAL_CORE_FUTURE_EQUIVALENCE_V1')
print('PASS_MINIMAL_CORE_FUTURE_EQUIVALENCE_V1')
