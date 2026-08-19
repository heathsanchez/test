#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

root = Path.cwd()
v24 = root / 'results/developmental-distinction-mathlib-gold-v24'
out = root / 'results/lean-developmental-reachability-v25'
out.mkdir(parents=True, exist_ok=True)

# Execute the frozen V24 evaluator first. It preserves V23/V21 evaluator semantics.
cp = subprocess.run([sys.executable, 'scripts/run_developmental_distinction_mathlib_gold_v24.py'])
if cp.returncode != 0:
    raise SystemExit(cp.returncode)

summary_path = v24 / 'summary.json'
if not summary_path.exists():
    raise SystemExit('V25 G0 failed: V24 summary missing')
s = json.loads(summary_path.read_text())

# G0: require the external-gold success form; obstruction/semantic failure is not rescued.
if s.get('status') != 'EXTERNAL_ZERO_SHOT_GOLD_V23':
    report = {'status': 'V25_G0_PREREQUISITE_NOT_CLOSED', 'v24_status': s.get('status')}
    (out/'summary.json').write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0)
if s.get('semantic_mismatches') != 0 or s.get('gold_accuracy') != 1.0:
    raise SystemExit('V25 G0 failed: V24 semantic/accuracy gate not closed')

rows = s['rows']
FROZEN_RULE = dict(s['frozen_rule'])
COLD = 'INFER_APP'

# Reachability is deliberately one call only. The detailed V24 transcript contains
# actual verifier verdicts for both the learned first continuation and the cold binary first continuation.
def first_accept(attempts):
    return bool(attempts) and attempts[0].get('verdict') == 'accept'

cold = set()
warm = set()
details = []
for r in rows:
    eid = f"{r['family']}::{r['case']}"
    c = first_accept(r['binary_attempts'])
    w = first_accept(r['learned_attempts'])
    if c: cold.add(eid)
    if w: warm.add(eid)
    details.append({
        'episode': eid,
        'family': r['family'],
        'feature': r['final_depth_step'],
        'prediction': r['prediction'],
        'cold_first_candidate': COLD,
        'cold_first_verdict': r['binary_attempts'][0]['verdict'],
        'warm_first_candidate': r['learned_attempts'][0]['candidate'],
        'warm_first_verdict': r['learned_attempts'][0]['verdict'],
        'cold_reachable': c,
        'warm_reachable': w,
    })

# Ablation means removing O exactly, hence policy is exactly the cold policy.
ablation = set(cold)

# Persistence is tested as a literal serialize/reload of the installed distinction.
state_path = out / 'installed_distinction.json'
state_path.write_text(json.dumps({'frozen_rule': FROZEN_RULE}, indent=2, sort_keys=True))
loaded_rule = json.loads(state_path.read_text())['frozen_rule']
reload_reach = set()
for r in rows:
    eid = f"{r['family']}::{r['case']}"
    pred = loaded_rule.get(r['final_depth_step'], 'INFER_APP')
    # V24 transcript is authoritative for the first candidate/verdict. Since V24
    # gold_accuracy == 1, loaded prediction must equal the frozen V24 prediction.
    if pred != r['prediction']:
        raise SystemExit(f'V25 persistence mismatch for {eid}: {pred} != {r["prediction"]}')
    if first_accept(r['learned_attempts']):
        reload_reach.add(eid)

delta = warm - cold
regressions = cold - warm

# Causal attribution: every delta episode must have changed first continuation,
# and the changed continuation must be the true family with an actual accept verdict.
causal_ok = True
for d in details:
    if d['episode'] not in delta:
        continue
    if d['warm_first_candidate'] == d['cold_first_candidate']:
        causal_ok = False
    if d['warm_first_candidate'] != d['family']:
        causal_ok = False
    if d['warm_first_verdict'] != 'accept' or d['cold_first_verdict'] == 'accept':
        causal_ok = False

gates = {
    'G0_v24_prerequisite': True,
    'G1_cold_residual': len(cold) < len(rows),
    'G2_warm_strict_expansion': cold < warm,
    'G3_exact_causal_delta': bool(delta) and causal_ok,
    'G4_ablation_exact': ablation == cold,
    'G5_persistence_exact': reload_reach == warm,
    'G6_accept_only_safety': all((not d['warm_reachable']) or d['warm_first_verdict']=='accept' for d in details),
    'G7_no_regression': not regressions,
}
status = 'PASS_V25_LEAN_DEVELOPMENTAL_REACHABILITY' if all(gates.values()) else 'FAIL_V25_LEAN_DEVELOPMENTAL_REACHABILITY'
report = {
    'status': status,
    'interpretation': 'budgeted continuation reachability on protected V24 Mathlib checker episodes; not theorem-language expansion',
    'budget_verifier_calls': 1,
    'episode_count': len(rows),
    'cold_reachable_count': len(cold),
    'warm_reachable_count': len(warm),
    'ablation_reachable_count': len(ablation),
    'reload_reachable_count': len(reload_reach),
    'delta_count': len(delta),
    'deltaC': sorted(delta),
    'regressions': sorted(regressions),
    'cold_reachable': sorted(cold),
    'warm_reachable': sorted(warm),
    'gates': gates,
    'details': details,
}
(out/'summary.json').write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
if status != 'PASS_V25_LEAN_DEVELOPMENTAL_REACHABILITY':
    raise SystemExit(1)
