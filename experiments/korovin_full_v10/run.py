from __future__ import annotations
from pathlib import Path
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
V9_RUN = HERE.parent / 'korovin_full_v9' / 'run.py'
spec = importlib.util.spec_from_file_location('v9_runtime', V9_RUN)
v9 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v9)

OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)
ROOT = 'KOROVIN_V10_PUBLIC_COMPLETION_TRANSFER_2026-08-22'


def finite_complete(world, base_rules, max_derivation_word_len=12):
    rules = list(base_rules)
    initial_cert = v9.global_certificate(
        world, v9.execute, rules,
        max_derivation_word_len=max_derivation_word_len,
    )
    initial_bad = v9.failed_edges(initial_cert)
    bound = len(initial_bad)
    additions = []

    for round_index in range(bound):
        cert = v9.global_certificate(
            world, v9.execute, rules,
            max_derivation_word_len=max_derivation_word_len,
        )
        bad = v9.failed_edges(cert)
        if not bad:
            break
        proposals = []
        for edge in bad:
            lhs = v9.decode(edge['lhs'])
            rhs = v9.decode(edge['rhs'])
            semantic_ok = v9.execute(world, lhs) == v9.execute(world, rhs)
            if not semantic_ok:
                continue
            proposals.append((
                len(lhs) + len(rhs),
                max(len(lhs), len(rhs)),
                lhs, rhs, edge,
            ))
        if not proposals:
            break
        proposals.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        _, _, lhs, rhs, edge = proposals[0]
        rule = (lhs, rhs)
        if rule in rules or (rhs, lhs) in rules:
            raise RuntimeError('failed edge proposed an already-present law')
        rules.append(rule)
        additions.append({
            'round': round_index + 1,
            'lhs': v9.fmt(lhs),
            'rhs': v9.fmt(rhs),
            'failed_edges_before': len(bad),
            'semantic_ok': semantic_ok,
            'residual_edge': {
                'representative': edge['representative'],
                'token': edge['token'],
                'lhs': edge['lhs'],
                'rhs': edge['rhs'],
            },
        })

    final_cert = v9.global_certificate(
        world, v9.execute, rules,
        max_derivation_word_len=max_derivation_word_len,
    )
    return rules, additions, initial_bad, final_cert


def run_world(index):
    phrase, seed, world = v9.make_world(ROOT, index)
    tokens = tuple(world.generators)
    semantic = lambda word: v9.execute(world, word)
    theory = v9.synthesize_theory(tokens, semantic, train_h=7, candidate_h=5, max_rules=10)
    base_rules = theory['rules']
    base_cert = v9.global_certificate(world, v9.execute, base_rules, max_derivation_word_len=12)

    if base_cert['global_completeness_theorem']:
        augmented_rules = list(base_rules)
        additions = []
        initial_bad = []
        augmented_cert = base_cert
    else:
        augmented_rules, additions, initial_bad, augmented_cert = finite_complete(
            world, base_rules, max_derivation_word_len=12
        )

    final_rules, deletions = v9.prune_globally_redundant_rules(
        world, v9.execute, augmented_rules, max_derivation_word_len=12
    )
    final_cert = v9.global_certificate(world, v9.execute, final_rules, max_derivation_word_len=12)
    final_bounded = v9.bounded_audit(world, final_rules, H=7)

    generated = []
    for add in additions:
        lhs, rhs = v9.decode(add['lhs']), v9.decode(add['rhs'])
        retained = any(r == (lhs, rhs) or r == (rhs, lhs) for r in final_rules)
        causal = None
        certified_after_removal = None
        if retained:
            idx = next(i for i, r in enumerate(final_rules) if r == (lhs, rhs) or r == (rhs, lhs))
            cert_without = v9.global_certificate(
                world, v9.execute,
                final_rules[:idx] + final_rules[idx + 1:],
                max_derivation_word_len=12,
            )
            causal = not cert_without['global_completeness_theorem']
            certified_after_removal = sum(e['valid'] for e in cert_without['edges'])
        generated.append({
            **add,
            'retained': retained,
            'causal': causal,
            'certified_edges_after_removal': certified_after_removal,
        })

    return {
        'index': index,
        'phrase': phrase,
        'seed_integer': seed,
        'generators': {k: list(v) for k, v in world.generators.items()},
        'state_count': final_cert['state_count'],
        'classification': 'baseline_complete' if base_cert['global_completeness_theorem'] else 'residual_bearing',
        'candidate_count': theory['candidate_count'],
        'base_train_audit': theory['train_audit'],
        'base_rules': [{'lhs': v9.fmt(a), 'rhs': v9.fmt(b)} for a, b in base_rules],
        'base_rules_sound': base_cert['rules_sound'],
        'initial_failed_edge_count': len(initial_bad),
        'residual_additions': additions,
        'completion_rounds': len(additions),
        'completion_within_bound': len(additions) <= len(initial_bad),
        'augmented_global': augmented_cert['global_completeness_theorem'],
        'global_pruning_deletions': deletions,
        'final_rules': [{'lhs': v9.fmt(a), 'rhs': v9.fmt(b)} for a, b in final_rules],
        'final_global': final_cert['global_completeness_theorem'],
        'final_rules_sound': final_cert['rules_sound'],
        'final_bounded_audit': final_bounded,
        'generated_rule_audit': generated,
        'retained_generated_count': sum(x['retained'] for x in generated),
    }


def main():
    worlds = []
    for i in range(12):
        print(f'V10 world {i}/11', flush=True)
        rec = run_world(i)
        worlds.append(rec)
        (OUT / 'PARTIAL.json').write_text(json.dumps(worlds, indent=2, sort_keys=True))
        print(json.dumps({
            'index': i,
            'states': rec['state_count'],
            'classification': rec['classification'],
            'initial_failed_edges': rec['initial_failed_edge_count'],
            'completion_rounds': rec['completion_rounds'],
            'retained_generated': rec['retained_generated_count'],
            'final_global': rec['final_global'],
        }, sort_keys=True), flush=True)

    residual = [w for w in worlds if w['classification'] == 'residual_bearing']
    retained = [x for w in residual for x in w['generated_rule_audit'] if x['retained']]
    gates = {
        'G0_exactly_twelve_worlds': len(worlds) == 12 and [w['index'] for w in worlds] == list(range(12)),
        'G1_inherited_rules_sound_every_world': all(w['base_rules_sound'] for w in worlds),
        'G2_generated_laws_sound': all(a['semantic_ok'] for w in residual for a in w['residual_additions']),
        'G3_residual_worlds_complete_within_initial_edge_bound': (
            bool(residual) and all(w['final_global'] and w['completion_within_bound'] for w in residual)
        ),
        'G4_no_additions_to_baseline_complete': all(
            w['classification'] != 'baseline_complete' or w['completion_rounds'] == 0 for w in worlds
        ),
        'G5_zero_false_merges_final_every_world': all(
            w['final_bounded_audit']['false_merges'] == 0 for w in worlds
        ),
        'G6_every_retained_generated_law_causal': bool(retained) and all(x['causal'] for x in retained),
        'G7_every_final_theory_globally_complete': all(w['final_global'] for w in worlds),
        'G8_at_least_one_residual_bearing_world': len(residual) >= 1,
        'G9_retained_generated_laws_compact_vs_states': all(
            w['retained_generated_count'] < w['state_count'] for w in residual
        ),
    }
    result = {
        'experiment': 'KOROVIN_FINITE_RESIDUAL_COMPLETION_V10',
        'precommit_sha256': hashlib.sha256((HERE / 'PRECOMMIT.md').read_bytes()).hexdigest(),
        'root_phrase': ROOT,
        'worlds': worlds,
        'residual_bearing_count': len(residual),
        'gates': gates,
        'all_gates_pass': all(gates.values()),
        'claim_boundary': (
            'Executable finite residual-edge completion with a data-derived bound equal to the initial '
            'failed canonical-edge count, tested on a frozen all-draws batch. The semantic oracle and '
            'finite canonical graph remain verifier-side infrastructure.'
        ),
    }
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    result['sha256'] = hashlib.sha256(raw).hexdigest()
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        'all_gates_pass': result['all_gates_pass'],
        'gates': gates,
        'state_counts': [w['state_count'] for w in worlds],
        'initial_failed_edges': [w['initial_failed_edge_count'] for w in worlds],
        'completion_rounds': [w['completion_rounds'] for w in worlds],
        'residual_bearing_count': len(residual),
        'sha256': result['sha256'],
    }, indent=2), flush=True)
    if not result['all_gates_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
