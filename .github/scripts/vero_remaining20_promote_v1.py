from pathlib import Path
import shutil, subprocess, re, json

BASE = Path('baseline28/galoistools_allin28').resolve()
OUT = Path('remaining20_promote_v1').resolve()
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE, OUT)

TARGETS = [
 'prove_div_identity','prove_div_unique','prove_div_deg_bound','prove_rem_idempotent',
 'prove_gcd_divides_both','prove_gcd_maximal','prove_powmod_reduced','prove_gcdex_bezout',
 'prove_rem_add_congr','prove_rem_mul_congr','prove_rem_coset_invariant','prove_exact_quo_mul',
 'prove_div_eval_reconstruction','prove_gcd_comm','prove_gcd_degree_le_inputs','prove_gcd_roots_common',
 'prove_gcdex_cofactor_deg_bound','prove_powmod_add_exponent','prove_powmod_mul_exponent','prove_powmod_frobenius'
]

def family(name):
    if 'powmod' in name: return 'powmod'
    if 'gcdex' in name: return 'gcdex'
    if 'gcd' in name: return 'gcd'
    return 'division_remainder'

def tactic(name):
    spec = name.replace('prove_','spec_')
    fam = family(name)
    tail = {
      'division_remainder': '[Galoistools.gfRem, Galoistools.gfQuo]',
      'gcd': '[Galoistools.gfRem]',
      'gcdex': '[]',
      'powmod': '[Galoistools.gfRem]'
    }[fam]
    if tail == '[]':
        return f"  simp only [{spec}, canonical]\n  intros\n  simp_all"
    return f"  simp only [{spec}, canonical]\n  intros\n  simp_all {tail}"

def patch_target(src, name, body):
    pat = re.compile(rf"(theorem {re.escape(name)} : [^\n]+ := by\n-- !benchmark @start proof def={re.escape(name)} kind=prove target=[^\n]+\n)(.*?)(\n-- !benchmark @end proof def={re.escape(name)})", re.S)
    m = pat.search(src)
    if not m: raise RuntimeError(f'cannot locate {name}')
    return src[:m.start()] + m.group(1) + body + m.group(3) + src[m.end():]

pf = OUT/'Galoistools/Proof/Division.lean'
txt = pf.read_text()
for name in TARGETS:
    txt = patch_target(txt, name, tactic(name))
pf.write_text(txt)

cp = subprocess.run(['lake','build'],cwd=OUT,text=True,capture_output=True)
raw = cp.stdout+'\n'+cp.stderr
print(raw[-12000:])
print('REMAINING20_PROMOTE_V1_EXIT', cp.returncode)
result = {'targets':len(TARGETS),'exit':cp.returncode}
(Path('remaining20_promote_result.json')).write_text(json.dumps(result,indent=2))
raise SystemExit(cp.returncode)
