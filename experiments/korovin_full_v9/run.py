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
from theory import synthesize_theory, saturate, audit_congruence, all_words
from certify import fmt, decode, global_certificate, prune_globally_redundant_rules

OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
SOURCE_ROOT = 'KOROVIN_V8_PUBLIC_BATCH_2026-08-22'
TRANSFER_ROOT = 'KOROVIN_V9_PUBLIC_RESIDUAL_TRANSFER_2026-08-22'


def make_world(root, index):
    phrase = f'{root}::{index}'
    seed = int.from_bytes(hashlib.sha256(phrase.encode()).digest()[:8], 'big')
    rng = random.Random(seed)
    n = 4
    generators = {
        'a': tuple(rng.randrange(n) for _ in range(n)),
        'b': tuple(rng.randrange(n) for _ in range(n)),
    }
    return phrase, seed, OpaqueWorld(f'v9_{index}', n, generators)


def bounded_audit(world, rules, H=7):
    tokens = tuple(world.generators)
    U, d = saturate(tokens, H, rules)
    return audit_congruence(U, d, lambda word: execute(world, word))


def failed_edges(cert):
    return [e for e in cert['edges'] if e['semantic_ok'] and not e['valid']]


def residual_edge_completion(world, base_rules, max_additions=8, max_derivation_word_len=12):
    rules = list(base_rules)
    additions = []
    for round_index in range(max_additions):
        cert = global_certificate(
            world, execute, rules,
            max_derivation_word_len=max_derivation_word_len,
        )
        bad = failed_edges(cert)
        if not bad:
            break
        proposals = []
        for edge in bad:
            lhs = decode(edge['lhs'])
            rhs = decode(edge['rhs'])
            semantic_ok = execute(world, lhs) == execute(world, rhs)
            if not semantic_ok:
                continue
            proposals.append((
                len(lhs) + len(rhs),
                max(len(lhs), len(rhs)),
                lhs,
                rhs,
                edge,
            ))
        if not proposals:
            break
        proposals.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        _, _, lhs, rhs, edge = proposals[0]
        rule = (lhs, rhs)
        if rule in rules or (rhs, lhs) in rules:
            break
        rules.append(rule)
        additions.append({
            'round': round_index + 1,
            'lhs': fmt(lhs),
            'rhs': fmt(rhs),
            'residual_edge': {
                'representative': edge['representative'],
                'token': edge['token'],
                'lhs': edge['lhs'],
                'rhs': edge['rhs'],
            },
            'failed_edges_before': len(bad),
            'semantic_ok': semantic_ok,
        })
    final_cert = global_certificate(
        world, execute, rules,
        max_derivation_word_len=max_derivation_word_len,
    )
    return rules, additions, final_cert


def causal_audit(world, final_rules, retained_generated, max_derivation_word_len=12):
    rows = []
    for generated in retained_generated:
        rule = (decode(generated['lhs']), decode(generated['rhs']))
        index = None
        for i, r in enumerate(final_rules):
            if r == rule or r == (rule[1], rule[0]):
                index = i
                break
        if index is None:
            rows.append({**generated, 'retained': False, 'causal': None})
            continue
        reduced = final_rules[:index] + final_rules[index + 1:]
        cert = global_certificate(
            world, execute, reduced,
            max_derivation_word_len=max_derivation_word_len,
        )
        rows.append({
            **generated,
            'retained': True,
            'causal': not cert['global_completeness_theorem'],
            'certified_edges_after_removal': sum(e['valid'] for e in cert['edges']),
            'edge_count': cert['edge_count'],
        })
    return rows


def run_world(root, index):
    phrase, seed, world = make_world(root, index)
    tokens = tuple(world.generators)
    semantic = lambda word: execute(world, word)

    theory = synthesize_theory(tokens, semantic, train_h=7, candidate_h=5, max_rules=10)
    base_rules = theory['rules']
    base_cert = global_certificate(world, execute, base_rules, max_derivation_word_len=9)
    base_bad = failed_edges(base_cert)

    if base_cert['global_completeness_theorem']:
        augmented_rules = list(base_rules)
        additions = []
        augmented_cert = base_cert
    else:
        augmented_rules, additions, augmented_cert = residual_edge_completion(
            world, base_rules, max_additions=8, max_derivation_word_len=12
        )

    final_rules, deletions = prune_globally_redundant_rules(
        world, execute, augmented_rules, max_derivation_word_len=12
    )
    final_cert = global_certificate(world, execute, final_rules, max_derivation_word_len=12)
    final_bounded = bounded_audit(world, final_rules, H=7)

    retained_generated = []
    for add in additions:
        lhs, rhs = decode(add['lhs']), decode(add['rhs'])
        retained = any(r == (lhs, rhs) or r == (rhs, lhs) for r in final_rules)
        retained_generated.append({**add, 'retained_after_pruning': retained})
    generated_causal = causal_audit(world, final_rules, retained_generated)

    return {
        'root': root,
        'index': index,
        'phrase': phrase,
        'seed_integer': seed,
        'generators': {k: list(v) for k, v in world.generators.items()},
        'state_count': base_cert['state_count'],
        'classification': 'baseline_complete' if base_cert['global_completeness_theorem'] else 'residual_bearing',
        'candidate_count': theory['candidate_count'],
        'base_train_audit': theory['train_audit'],
        'base_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in base_rules],
        'base_global': base_cert['global_completeness_theorem'],
        'base_failed_edges': [{k: e[k] for k in ('representative','token','lhs','rhs','semantic_ok','valid')} for e in base_bad],
        'residual_additions': additions,
        'augmented_global': augmented_cert['global_completeness_theorem'],
        'global_pruning_deletions': deletions,
        'final_rules': [{'lhs': fmt(a), 'rhs': fmt(b)} for a, b in final_rules],
        'final_bounded_audit': final_bounded,
        'final_global_certificate': {k: v for k, v in final_cert.items() if k != 'edges'},
        'generated_rule_causality': generated_causal,
        'checks': {
            'base_rules_sound': base_cert['rules_sound'],
            'all_added_rules_sound': all(a['semantic_ok'] for a in additions),
            'final_rules_sound': final_cert['rules_sound'],
            'final_global': final_cert['global_completeness_theorem'],
            'final_zero_false_merges': final_bounded['false_merges'] == 0,
            'baseline_complete_no_additions': (not base_cert['global_completeness_theorem']) or len(additions) == 0,
            'all_retained_generated_causal': all(
                (not x['retained']) or x['causal'] for x in generated_causal
            ),
        },
    }


def source_gate():
    rec = run_world(SOURCE_ROOT, 7)
    expected_rules = [
        {'lhs': 'abb', 'rhs': 'bbb'},
        {'lhs': 'a', 'rhs': 'aba'},
        {'lhs': 'a', 'rhs': 'aaa'},
        {'lhs': 'bbb', 'rhs': 'bbbb'},
        {'lhs': 'bb', 'rhs': 'bbab'},
    ]
    expected_edge = {'representative': 'abbaa', 'token': 'b', 'lhs': 'abbaab', 'rhs': 'abba'}
    reproduced = (
        rec['state_count'] == 17
        and rec['base_train_audit']['semantic_classes'] == 17
        and rec['base_train_audit']['congruence_classes'] == 18
        and rec['base_train_audit']['false_merges'] == 0
        and rec['base_rules'] == expected_rules
        and len(rec['base_failed_edges']) == 1
        and all(rec['base_failed_edges'][0][k] == v for k, v in expected_edge.items())
    )
    exact_generated = (
        len(rec['residual_additions']) == 1
        and rec['residual_additions'][0]['lhs'] == 'abbaab'
        and rec['residual_additions'][0]['rhs'] == 'abba'
    )
    return rec, reproduced, exact_generated


def main():
    source, source_reproduced, exact_generated = source_gate()
    transfer = []
    for i in range(12):
        print(f'V9 transfer world {i}/11', flush=True)
        rec = run_world(TRANSFER_ROOT, i)
        transfer.append(rec)
        (OUT / 'PARTIAL.json').write_text(json.dumps({'source': source, 'transfer': transfer}, indent=2, sort_keys=True))
        print(json.dumps({
            'index': i,
            'states': rec['state_count'],
            'classification': rec['classification'],
            'base_failed_edges': len(rec['base_failed_edges']),
            'additions': len(rec['residual_additions']),
            'final_global': rec['checks']['final_global'],
            'final_classes': rec['final_bounded_audit']['congruence_classes'],
            'semantic_classes': rec['final_bounded_audit']['semantic_classes'],
        }, sort_keys=True), flush=True)

    residual_bearing = [w for w in transfer if w['classification'] == 'residual_bearing']
    retained_generated = [
        x for w in residual_bearing for x in w['generated_rule_causality'] if x['retained']
    ]

    gates = {
        'G0_v8_source_reproduced_exactly': source_reproduced,
        'G1_source_residual_generates_exact_missing_law': exact_generated,
        'G2_source_bounded_18_to_17_zero_false_merges': (
            source['base_train_audit']['congruence_classes'] == 18
            and source['final_bounded_audit']['congruence_classes'] == 17
            and source['final_bounded_audit']['semantic_classes'] == 17
            and source['final_bounded_audit']['false_merges'] == 0
        ),
        'G3_source_global_completion': source['checks']['final_global'],
        'G4_source_generated_law_sound_and_causal': (
            source['checks']['all_added_rules_sound']
            and any(x['retained'] and x['causal'] for x in source['generated_rule_causality'])
        ),
        'G5_exactly_twelve_transfer_draws_reported': (
            len(transfer) == 12 and [w['index'] for w in transfer] == list(range(12))
        ),
        'G6_transfer_contains_residual_bearing_world': len(residual_bearing) >= 1,
        'G7_every_residual_bearing_world_repaired_globally': (
            bool(residual_bearing) and all(w['checks']['final_global'] for w in residual_bearing)
        ),
        'G8_every_added_transfer_law_semantically_sound': all(
            w['checks']['all_added_rules_sound'] for w in residual_bearing
        ),
        'G9_every_retained_generated_transfer_law_causal': (
            bool(retained_generated) and all(x['causal'] for x in retained_generated)
        ),
        'G10_zero_false_merges_final_every_transfer_world': all(
            w['checks']['final_zero_false_merges'] for w in transfer
        ),
        'G11_no_additions_to_baseline_complete_worlds': all(
            w['checks']['baseline_complete_no_additions'] for w in transfer
        ),
    }

    result = {
        'experiment': 'KOROVIN_RESIDUAL_LAW_COMPLETION_V9',
        'precommit_sha256': hashlib.sha256((HERE / 'PRECOMMIT.md').read_bytes()).hexdigest(),
        'source': source,
        'transfer_root': TRANSFER_ROOT,
        'transfer': transfer,
        'transfer_residual_bearing_count': len(residual_bearing),
        'gates': gates,
        'all_gates_pass': all(gates.values()),
        'claim_boundary': (
            'A verified incompleteness residual is converted into the shortest semantically validated '
            'failed-edge equation, outside the original candidate-side horizon, and reused unchanged '
            'on a publicly frozen all-draws transfer batch. Not historical novelty or human usefulness.'
        ),
    }
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    result['sha256'] = hashlib.sha256(raw).hexdigest()
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        'all_gates_pass': result['all_gates_pass'],
        'gates': gates,
        'source_added': source['residual_additions'],
        'transfer_residual_bearing_count': len(residual_bearing),
        'transfer_state_counts': [w['state_count'] for w in transfer],
        'transfer_addition_counts': [len(w['residual_additions']) for w in transfer],
        'sha256': result['sha256'],
    }, indent=2), flush=True)
    if not result['all_gates_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
