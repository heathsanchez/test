from pathlib import Path
import os, re, json

selftxt = Path('results/v40/callgrind-self.txt').read_text(errors='replace')
m = re.search(r'^\s*([0-9,]+)\s+\(100\.0%\)\s+PROGRAM TOTALS', selftxt, re.M)
if not m:
    raise SystemExit('NO_PROGRAM_TOTALS')
total = int(m.group(1).replace(',', ''))
baseline = int(os.environ['V39_DIAG_IR'])
perturb = 100 * (total - baseline) / baseline
perturb_ok = abs(perturb) <= 3.0

txt = Path('results/v40/callgrind-inclusive.txt').read_text(errors='replace')
names = ['app', 'var', 'sort', 'const', 'lambda', 'pi', 'let', 'proj', 'literal']
rows = {}
for name in names:
    pat = re.compile(r'^\s*([0-9,]+)\s+\([^\n]*\)\s+.*v40_diag_' + name + r'[^\n]*$', re.M)
    vals = [int(x.replace(',', '')) for x in pat.findall(txt)]
    if vals:
        v = max(vals)
        rows[name] = {'inclusive_ir': v, 'whole_pct': 100 * v / total}

material = {k: v for k, v in rows.items() if v['whole_pct'] >= 0.5}
observable = len(rows) >= 5 and bool(material)
if observable and perturb_ok:
    verdict = 'CASE_BOUNDARIES_OBSERVED'
    nxt = 'rank case families by whole-Mathlib mass; freeze smallest A/B intervention only for a case with plausible >=5% whole-program opportunity'
elif observable:
    verdict = 'CASE_BOUNDARIES_OBSERVED_BUT_PERTURBED'
    nxt = 'use ranking qualitatively only; build lower-overhead boundary mechanism before intervention'
else:
    verdict = 'CASE_BOUNDARIES_STILL_HIDDEN'
    nxt = 'stop Callgrind boundary attempts; use explicit counters plus controlled per-case exclusion/sham measurements'

out = {
    'verdict': verdict,
    'program_total_ir': total,
    'v39_baseline_ir': baseline,
    'perturbation_pct': perturb,
    'perturbation_ok': perturb_ok,
    'inclusive_case_rows': rows,
    'material_cases_ge_0_5pct': material,
    'frozen_next': nxt,
}
Path('results/v40/verdict.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
