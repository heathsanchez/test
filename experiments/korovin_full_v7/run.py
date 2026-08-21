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

PHRASE = 'KOROVIN_V7_PUBLIC_VALIDATION_2026-08-22'
seed = int.from_bytes(hashlib.sha256(PHRASE.encode()).digest()[:8], 'big')
rng = random.Random(seed)
n = 4
generators = {
    'a': tuple(rng.randrange(n) for _ in range(n)),
    'b': tuple(rng.randrange(n) for _ in range(n)),
}
world = OpaqueWorld('v7_public_precommitted_validation', n, generators)
tokens = tuple(world.generators)
semantic = lambda word: execute(world, word)


def is_permutation(t):
    return len(set(t)) == len(t)


v5 = synthesize_theory(tokens, semantic, train_h=7, candidate_h=5, max_rules=10)
initial_rules = v5['rules']
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

gates = {
    'G0_nontrivial_state_count': final_cert['state_count'] >= 6,
    'G1_at_least_one_generator_noninvertible': not all(
        is_permutation(t) for t in generators.values()
    ),
    'G2_bounded_theory_exact': (
        v5['train_audit']['exact'] and v5['train_audit']['false_merges'] == 0
    ),
    'G3_initial_global_certificate': initial_cert['global_completeness_theorem'],
    'G4_pruned_global_certificate': final_cert['global_completeness_theorem'],
    'G5_every_final_rule_causal': all(
        not x['global_after_removal'] for x in ablations
    ),
    'G6_compact_rule_count_lt_state_count': len(final_rules) < final_cert['state_count'],
    'G7_all_final_rules_sound': final_cert['rules_sound'],
    'G8_all_edges_explicitly_certified': final_cert['all_edges_certified'],
}

result = {
    'experiment': 'KOROVIN_PUBLIC_SYNTHETIC_UNNAMED_OBJECT_V7',
    'precommit_sha256': hashlib.sha256((HERE / 'PRECOMMIT.md').read_bytes()).hexdigest(),
    'seed_phrase': PHRASE,
    'seed_integer': seed,
    'generators': {k: list(v) for k, v in generators.items()},
    'gates': gates,
    'all_gates_pass': all(gates.values()),
    'bounded_theory': {
        'candidate_count': v5['candidate_count'],
        'rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in initial_rules],
        'train_audit': v5['train_audit'],
        'history': v5['history'],
    },
    'initial_global_certificate': {
        k: v for k, v in initial_cert.items() if k != 'edges'
    },
    'global_pruning_deletions': deletions,
    'final_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in final_rules],
    'final_global_certificate': final_cert,
    'final_rule_ablation': ablations,
    'claim_boundary': (
        'Fresh publicly precommitted unlabeled synthetic finite transformation object; '
        'global finite presentation certificate relative to exact semantics. '
        'Not a claim of historical mathematical novelty.'
    ),
}
raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
result['sha256'] = hashlib.sha256(raw).hexdigest()
(OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))

print(json.dumps({
    'seed_integer': seed,
    'generators': result['generators'],
    'all_gates_pass': result['all_gates_pass'],
    'gates': gates,
    'state_count': final_cert['state_count'],
    'initial_rules': result['bounded_theory']['rules'],
    'global_pruning_deletions': deletions,
    'final_rules': result['final_rules'],
    'global_certificate': {
        k: v for k, v in final_cert.items() if k != 'edges'
    },
    'ablation': ablations,
    'result_sha256': result['sha256'],
}, indent=2))

if not result['all_gates_pass']:
    raise SystemExit(1)
