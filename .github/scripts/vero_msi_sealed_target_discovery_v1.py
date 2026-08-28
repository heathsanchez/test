from pathlib import Path
import hashlib, itertools, json, re, shutil, subprocess

BASE = Path('baseline28/galoistools_allin28').resolve()
ROOT = Path('vero_msi_sealed_target_discovery_v1').resolve()
if ROOT.exists(): shutil.rmtree(ROOT)
ROOT.mkdir()

TARGETS = [
 'prove_div_identity','prove_div_unique','prove_div_deg_bound','prove_rem_idempotent',
 'prove_gcd_divides_both','prove_gcd_maximal','prove_powmod_reduced','prove_gcdex_bezout',
 'prove_rem_add_congr','prove_rem_mul_congr','prove_rem_coset_invariant','prove_exact_quo_mul',
 'prove_div_eval_reconstruction','prove_gcd_comm','prove_gcd_degree_le_inputs','prove_gcd_roots_common',
 'prove_gcdex_cofactor_deg_bound','prove_powmod_add_exponent','prove_powmod_mul_exponent','prove_powmod_frobenius'
]

# Frozen before any selected-target compilation.  The commit is the immutable
# pre-existing repo state from which the remaining-20 census was inspected.
SEED = '2a474010775d08bb5eeed4791fe8ac8f6d0226ad|MSI_SEALED_V1'
DIGEST = hashlib.sha256(SEED.encode()).hexdigest()
INDEX = int(DIGEST, 16) % len(TARGETS)
TARGET = TARGETS[INDEX]
SPEC = TARGET.replace('prove_', 'spec_')
BUDGET = 24

print('SEALED_SELECTION', json.dumps({'seed':SEED,'sha256':DIGEST,'index':INDEX,'target':TARGET,'budget':BUDGET}, sort_keys=True))

# This entire candidate family is target-agnostic apart from substituting the
# target's own spec theorem name.  No candidates are added after seeing the
# selected target's compiler output.
DEFS = [
 'Galoistools.gfRem','Galoistools.gfQuo','Galoistools.gfDiv','Galoistools.gfGcd',
 'Galoistools.gfGcdex','Galoistools.gfPowMod','Galoistools.gfMul','Galoistools.gfAdd'
]

CANDIDATES = [
 ('push', f'  simp only [{SPEC}, canonical]\n  intros\n  simp_all'),
 ('push_rem', f'  simp only [{SPEC}, canonical]\n  intros\n  simp_all [Galoistools.gfRem]'),
 ('push_gcd', f'  simp only [{SPEC}, canonical]\n  intros\n  simp_all [Galoistools.gfGcd]'),
 ('push_rem_gcd', f'  simp only [{SPEC}, canonical]\n  intros\n  simp_all [Galoistools.gfRem, Galoistools.gfGcd]'),
]
# Frozen systematic interface-expansion family: singles then pairs, in the
# fixed global DEFS order.  These candidates do not depend on diagnostics.
for r in (1, 2):
    for combo in itertools.combinations(DEFS, r):
        label = 'iface_' + '_'.join(x.split('.')[-1] for x in combo)
        defs = ', '.join(combo)
        CANDIDATES.append((label, f'  simp only [{SPEC}, canonical]\n  intros\n  simp_all [{defs}]'))
CANDIDATES = CANDIDATES[:BUDGET]


def patch_target(src: str, name: str, body: str) -> str:
    pat = re.compile(rf'(theorem {re.escape(name)} : [^\n]+ := by\n-- !benchmark @start proof def={re.escape(name)} kind=prove target=[^\n]+\n)(.*?)(\n-- !benchmark @end proof def={re.escape(name)})', re.S)
    m = pat.search(src)
    if not m: raise RuntimeError(f'cannot locate benchmark target {name}')
    return src[:m.start()] + m.group(1) + body + m.group(3) + src[m.end():]


def isolate_selected(original: str) -> str:
    """Neutralize only the other pre-existing unsolved benchmark targets.

    V1 initially compiled the whole 20-residual file, so unrelated unsolved
    targets made every candidate red.  This harness fix changes no selected
    target, candidate, budget, or oracle.  `sorry` is used only for the other
    19 benchmark holes so process success is exactly the selected theorem gate.
    """
    src = original
    for name in TARGETS:
        if name != TARGET:
            src = patch_target(src, name, '  sorry')
    return src


def run_candidate(i, label, body):
    wd = ROOT / f'{i:02d}_{label}'
    shutil.copytree(BASE, wd)
    for c in wd.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf = wd/'Galoistools/Proof/Division.lean'
    isolated = isolate_selected(pf.read_text())
    pf.write_text(patch_target(isolated, TARGET, body))
    cp = subprocess.run(['lake','lean','Galoistools/Proof/Division.lean'], cwd=wd, text=True, capture_output=True, timeout=180)
    raw = cp.stdout + '\n' + cp.stderr
    # Diagnostics are recorded only after the run for scientific audit; the
    # search policy never reads them and candidate ordering is already frozen.
    errors = [x.strip() for x in raw.splitlines() if 'error:' in x or 'error(' in x]
    return {'index':i,'label':label,'exit':cp.returncode,'success':cp.returncode==0,'error_count':len(errors),'error_tail':errors[-6:]}

rows=[]
winner=None
for i,(label,body) in enumerate(CANDIDATES,1):
    row=run_candidate(i,label,body)
    rows.append(row)
    print('SEALED_PROBE', json.dumps({k:row[k] for k in ('index','label','exit','error_count')}, sort_keys=True))
    if row['success']:
        winner={'index':i,'label':label,'body':body}
        break

result={
 'schema':'msi.vero-sealed-target-discovery.v1-isolated',
 'selection':{'seed':SEED,'sha256':DIGEST,'index':INDEX,'target':TARGET},
 'candidate_policy':'frozen target-agnostic push + systematic interface expansion; compiler diagnostics not read by policy',
 'harness_fix':'other 19 pre-existing residual targets replaced by sorry solely to isolate selected theorem exit status',
 'budget':BUDGET,
 'queries_used':len(rows),
 'success':winner is not None,
 'winner':winner,
 'rows':rows,
}
(ROOT/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True))
if winner:
    (ROOT/'DISCOVERED_PROOF.lean.txt').write_text(winner['body']+'\n')
    print('PASS_SEALED_SOURCE_DISTINCT_DISCOVERY', json.dumps({'target':TARGET,'queries':len(rows),'winner':winner['label']}, sort_keys=True))
else:
    print('SEALED_DISCOVERY_RESIDUAL', json.dumps({'target':TARGET,'queries':len(rows),'last_error_count':rows[-1]['error_count'] if rows else None}, sort_keys=True))
    raise SystemExit(2)
