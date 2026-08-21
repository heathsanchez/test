from __future__ import annotations
from pathlib import Path
import hashlib
import json
import random
import sys

HERE = Path(__file__).resolve().parent
V5 = HERE.parent / 'korovin_full_v5'
V6 = HERE.parent / 'korovin_full_v6'
sys.path.insert(0, str(V5))
sys.path.insert(0, str(V6))

from worlds import OpaqueWorld, execute
from theory import synthesize_theory
from certify import fmt, global_certificate, prune_globally_redundant_rules

OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
ROOT = 'KOROVIN_V8_PUBLIC_BATCH_2026-08-22'


def is_permutation(t):
    return len(set(t)) == len(t)


def make_world(index):
    phrase = f'{ROOT}::{index}'
    seed = int.from_bytes(hashlib.sha256(phrase.encode()).digest()[:8], 'big')
    rng = random.Random(seed)
    n = 4
    generators = {
        'a': tuple(rng.randrange(n) for _ in range(n)),
        'b': tuple(rng.randrange(n) for _ in range(n)),
    }
    return phrase, seed, OpaqueWorld(f'v8_public_batch_{index}', n, generators)


def run_world(index):
    phrase, seed, world = make_world(index)
    tokens = tuple(world.generators)
    semantic = lambda word: execute(world, word)

    theory = synthesize_theory(tokens, semantic, train_h=7, candidate_h=5, max_rules=10)
    initial_rules = theory['rules']
    initial_cert = global_certificate(world, execute, initial_rules, max_derivation_word_len=9)
    final_rules, deletions = prune_globally_redundant_rules(
        world, execute, initial_rules, max_derivation_word_len=9
    )
    final_cert = global_certificate(world, execute, final_rules, max_derivation_word_len=9)

    ablations = []
    for i, rule in enumerate(final_rules):
        reduced = final_rules[:i] + final_rules[i + 1:]
        cert = global_certificate(world, execute, reduced, max_derivation_word_len=9)
        ablations.append({
            'removed': {'lhs': fmt(rule[0]), 'rhs': fmt(rule[1])},
            'global_after_removal': cert['global_completeness_theorem'],
            'certified_edges_after_removal': sum(e['valid'] for e in cert['edges']),
            'edge_count': cert['edge_count'],
        })

    state_count = final_cert['state_count']
    nontrivial = state_count >= 6
    record = {
        'index': index,
        'phrase': phrase,
        'seed_integer': seed,
        'generators': {k: list(v) for k, v in world.generators.items()},
        'primitive_permutation_flags': {
            k: is_permutation(v) for k, v in world.generators.items()
        },
        'state_count': state_count,
        'stratum': 'nontrivial' if nontrivial else 'trivial',
        'candidate_count': theory['candidate_count'],
        'bounded_train_audit': theory['train_audit'],
        'initial_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in initial_rules],
        'initial_global_certificate': {
            k: v for k, v in initial_cert.items() if k != 'edges'
        },
        'global_pruning_deletions': deletions,
        'final_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in final_rules],
        'final_global_certificate': final_cert,
        'final_rule_ablation': ablations,
        'world_checks': {
            'rules_sound': final_cert['rules_sound'],
            'zero_false_merges': theory['train_audit']['false_merges'] == 0,
            'bounded_exact': theory['train_audit']['exact'],
            'initial_global': initial_cert['global_completeness_theorem'],
            'pruned_global': final_cert['global_completeness_theorem'],
            'all_final_rules_causal': all(not x['global_after_removal'] for x in ablations),
            'all_edges_certified': final_cert['all_edges_certified'],
            'compact': len(final_rules) < state_count,
        },
    }
    return record


def main():
    worlds = []
    for i in range(8):
        print(f'V8 world {i}/7: generating fixed indexed draw', flush=True)
        rec = run_world(i)
        worlds.append(rec)
        (OUT / 'PARTIAL.json').write_text(json.dumps(worlds, indent=2, sort_keys=True))
        print(json.dumps({
            'index': i,
            'state_count': rec['state_count'],
            'stratum': rec['stratum'],
            'final_rule_count': len(rec['final_rules']),
            'checks': rec['world_checks'],
        }, sort_keys=True), flush=True)

    nontrivial = [w for w in worlds if w['stratum'] == 'nontrivial']
    gates = {
        'G0_exactly_eight_worlds_reported': len(worlds) == 8 and [w['index'] for w in worlds] == list(range(8)),
        'G1_at_least_four_nontrivial': len(nontrivial) >= 4,
        'G2_soundness_every_draw': all(w['world_checks']['rules_sound'] for w in worlds),
        'G3_zero_false_merges_every_draw': all(w['world_checks']['zero_false_merges'] for w in worlds),
        'G4_bounded_exact_every_nontrivial': bool(nontrivial) and all(w['world_checks']['bounded_exact'] for w in nontrivial),
        'G5_initial_global_every_nontrivial': bool(nontrivial) and all(w['world_checks']['initial_global'] for w in nontrivial),
        'G6_pruned_global_every_nontrivial': bool(nontrivial) and all(w['world_checks']['pruned_global'] for w in nontrivial),
        'G7_final_rules_causal_every_nontrivial': bool(nontrivial) and all(w['world_checks']['all_final_rules_causal'] for w in nontrivial),
        'G8_edges_certified_every_nontrivial': bool(nontrivial) and all(w['world_checks']['all_edges_certified'] for w in nontrivial),
        'G9_compact_every_nontrivial': bool(nontrivial) and all(w['world_checks']['compact'] for w in nontrivial),
    }

    result = {
        'experiment': 'KOROVIN_BATCH_TRANSFER_V8',
        'precommit_sha256': hashlib.sha256((HERE / 'PRECOMMIT.md').read_bytes()).hexdigest(),
        'root_phrase': ROOT,
        'gates': gates,
        'all_gates_pass': all(gates.values()),
        'world_count': len(worlds),
        'nontrivial_count': len(nontrivial),
        'trivial_count': len(worlds) - len(nontrivial),
        'worlds': worlds,
        'claim_boundary': (
            'Publicly precommitted all-draws distributional transfer across eight unlabeled '
            'synthetic finite transformation worlds, with no seed replacement. '
            'Not historical mathematical novelty or external human usefulness.'
        ),
    }
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    result['sha256'] = hashlib.sha256(raw).hexdigest()
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        'all_gates_pass': result['all_gates_pass'],
        'gates': gates,
        'state_counts': [w['state_count'] for w in worlds],
        'strata': [w['stratum'] for w in worlds],
        'final_rule_counts': [len(w['final_rules']) for w in worlds],
        'nontrivial_count': len(nontrivial),
        'sha256': result['sha256'],
    }, indent=2), flush=True)
    if not result['all_gates_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
