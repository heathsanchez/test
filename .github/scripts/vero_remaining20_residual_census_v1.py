from pathlib import Path
import shutil, subprocess, json, re, collections

BASE = Path('baseline28/galoistools_allin28').resolve()
OUT = Path('remaining20_census_v1').resolve()
OUT.mkdir(exist_ok=True)

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

rows=[]
for i,name in enumerate(TARGETS):
    wd = OUT/name
    if wd.exists(): shutil.rmtree(wd)
    shutil.copytree(BASE, wd)
    pf = wd/'Galoistools/Proof/Division.lean'
    txt = pf.read_text()
    pf.write_text(patch_target(txt,name,tactic(name)))
    cp = subprocess.run(['lake','build'],cwd=wd,text=True,capture_output=True)
    raw = cp.stdout+'\n'+cp.stderr
    errs = [x.strip() for x in re.findall(r'error:(.*?)(?=\n[^\n]*?(?:error:|warning:)|\Z)', raw, re.S)]
    tail = '\n'.join(errs[-6:])[-16000:]
    if not tail and cp.returncode != 0:
        tail = '\n'.join(raw.splitlines()[-120:])[-16000:]
    tokens = {}
    for k in ['gfDiv','gfRem','gfGcd','gfGcdex','gfPowMod','gfMul','gfAdd','refGfDegree','refPolyEval','IsNorm','leadCoeff']:
        tokens[k]=tail.count(k)
    rows.append({'target':name,'family':family(name),'exit':cp.returncode,'residual':tail,'tokens':tokens})
    print('CENSUS',i+1,len(TARGETS),name,'EXIT',cp.returncode)
    if tail: print(tail[-2200:])

failed=[r for r in rows if r['exit']!=0]
fanout=collections.Counter()
for r in failed:
    for k,v in r['tokens'].items():
        if v: fanout[k]+=1
family_counts=collections.Counter(r['family'] for r in failed)
result={
 'targets':len(rows),
 'closed_by_push':sum(r['exit']==0 for r in rows),
 'failed':len(failed),
 'family_counts':dict(family_counts),
 'interface_fanout':fanout.most_common(),
 'rows':rows
}
(OUT/'census.json').write_text(json.dumps(result,indent=2))
print('REMAINING20_CENSUS_V1',json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
