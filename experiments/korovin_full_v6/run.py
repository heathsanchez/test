from __future__ import annotations
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
V5 = HERE.parent / 'korovin_full_v5'
sys.path.insert(0, str(V5))
sys.path.insert(0, str(HERE))

from worlds import source_world, transfer_world, execute
from theory import synthesize_theory
from certify import fmt, global_certificate, prune_globally_redundant_rules

OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)


def learn_and_certify(world):
    tokens = tuple(world.generators)
    semantic = lambda word: execute(world, word)
    v5 = synthesize_theory(tokens, semantic, train_h=7, candidate_h=4, max_rules=8)
    initial_rules = v5['rules']
    initial_cert = global_certificate(world, execute, initial_rules, max_derivation_word_len=7)

    final_rules, deletions = prune_globally_redundant_rules(
        world, execute, initial_rules, max_derivation_word_len=7
    )
    final_cert = global_certificate(world, execute, final_rules, max_derivation_word_len=7)

    ablations = []
    for i, rule in enumerate(final_rules):
        reduced = final_rules[:i] + final_rules[i + 1:]
        cert = global_certificate(world, execute, reduced, max_derivation_word_len=7)
        ablations.append({
            'removed': {'lhs': fmt(rule[0]), 'rhs': fmt(rule[1])},
            'global_completeness_after_removal': cert['global_completeness_theorem'],
            'certified_edges_after_removal': sum(edge['valid'] for edge in cert['edges']),
            'edge_count': cert['edge_count'],
        })

    return {
        'tag': world.tag,
        'v5_initial_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in initial_rules],
        'v5_initial_global_certificate': {
            k: v for k, v in initial_cert.items() if k != 'edges'
        },
        'global_pruning_deletions': deletions,
        'final_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in final_rules],
        'final_certificate': final_cert,
        'final_rule_ablation': ablations,
    }


def main():
    source = learn_and_certify(source_world())
    transfer = learn_and_certify(transfer_world())

    gates = {
        'G1_source_rules_sound': source['final_certificate']['rules_sound'],
        'G2_source_all_generator_edges_certified': source['final_certificate']['all_edges_certified'],
        'G3_source_global_completeness': source['final_certificate']['global_completeness_theorem'],
        'G4_source_final_rules_causally_minimal': all(
            not x['global_completeness_after_removal'] for x in source['final_rule_ablation']
        ),
        'G5_source_compact': len(source['final_rules']) <= 3,
        'G6_transfer_rules_sound': transfer['final_certificate']['rules_sound'],
        'G7_transfer_all_generator_edges_certified': transfer['final_certificate']['all_edges_certified'],
        'G8_transfer_global_completeness': transfer['final_certificate']['global_completeness_theorem'],
        'G9_transfer_final_rules_causally_minimal': all(
            not x['global_completeness_after_removal'] for x in transfer['final_rule_ablation']
        ),
        'G10_transfer_compact': len(transfer['final_rules']) <= 3,
    }

    result = {
        'experiment': 'KOROVIN_GLOBAL_PRESENTATION_CERTIFICATE_V6',
        'theorem_schema': (
            'If every retained relation is semantically sound, the empty word is the canonical '
            'representative of the start state, and for every reachable canonical state q and '
            'generator a there is a certified derivation r_q a = r_delta(q,a), then by induction '
            'every finite word is congruent to the canonical representative of its semantic state. '
            'Soundness gives the converse, so generated congruence equals semantic equivalence for all words.'
        ),
        'claim_boundary': (
            'This is a global completeness certificate for the two declared finite generated '
            'transformation worlds, relative to exact external semantics and the learned relations. '
            'It is not evidence of historically novel mathematics or unrestricted theorem discovery.'
        ),
        'gates': gates,
        'all_gates_pass': all(gates.values()),
        'source': source,
        'transfer': transfer,
    }
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    result['sha256'] = hashlib.sha256(raw).hexdigest()
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))

    print(json.dumps({
        'all_gates_pass': result['all_gates_pass'],
        'gates': gates,
        'source': {
            'initial_rules': source['v5_initial_rules'],
            'deletions': source['global_pruning_deletions'],
            'final_rules': source['final_rules'],
            'certificate': {k:v for k,v in source['final_certificate'].items() if k != 'edges'},
            'ablation': source['final_rule_ablation'],
            'edge_step_counts': [e['steps'] for e in source['final_certificate']['edges']],
        },
        'transfer': {
            'initial_rules': transfer['v5_initial_rules'],
            'deletions': transfer['global_pruning_deletions'],
            'final_rules': transfer['final_rules'],
            'certificate': {k:v for k,v in transfer['final_certificate'].items() if k != 'edges'},
            'ablation': transfer['final_rule_ablation'],
            'edge_step_counts': [e['steps'] for e in transfer['final_certificate']['edges']],
        },
        'sha256': result['sha256'],
    }, indent=2))

    if not result['all_gates_pass']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
