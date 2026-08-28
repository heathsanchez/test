from pathlib import Path
import json, re, subprocess, sys

ROOT = Path('full48/remaining20_promote_v1').resolve()
if not ROOT.exists():
    raise SystemExit('missing promoted full48 artifact')

proof_files = sorted((ROOT/'Galoistools'/'Proof').glob('*.lean'))
start_re = re.compile(r'-- !benchmark @start proof def=([A-Za-z0-9_]+) kind=prove[^\n]*\n')
end_tpl = '-- !benchmark @end proof def={}'

entries = []
for pf in proof_files:
    src = pf.read_text()
    for m in start_re.finditer(src):
        name = m.group(1)
        end = src.find(end_tpl.format(name), m.end())
        if end < 0:
            raise RuntimeError(f'missing end marker for {name} in {pf}')
        body = src[m.end():end]
        entries.append((pf, name, body))

all_names = {name for _, name, _ in entries}
unsafe_tokens = ('sorry', 'admit', 'axiom', 'unsafe')
violations = []
cross_refs = []
spec_refs = {}

for pf, name, body in entries:
    low = body.lower()
    bad = [tok for tok in unsafe_tokens if re.search(rf'\b{re.escape(tok)}\b', low)]
    if bad:
        violations.append({'target': name, 'kind': 'unsafe_token', 'tokens': bad})
    refs = sorted(other for other in all_names if other != name and re.search(rf'\b{re.escape(other)}\b', body))
    if refs:
        cross_refs.append({'target': name, 'refs': refs})
    specs = sorted(set(re.findall(r'\bspec_[A-Za-z0-9_]+\b', body)))
    if specs:
        spec_refs[name] = specs

# Re-run the complete promoted project from a clean build state.
subprocess.run(['lake', 'clean'], cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cp = subprocess.run(['lake', 'build'], cwd=ROOT, text=True, capture_output=True)
print((cp.stdout + '\n' + cp.stderr)[-12000:])

result = {
    'proof_blocks': len(entries),
    'proof_files': [str(p.relative_to(ROOT)) for p in proof_files],
    'unsafe_violations': violations,
    'cross_target_references': cross_refs,
    'targets_with_spec_refs': len(spec_refs),
    'spec_refs': spec_refs,
    'clean_full_build_exit': cp.returncode,
}
Path('full48_independence_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True))
print('FULL48_INDEPENDENCE_AUDIT_V1', json.dumps({
    'proof_blocks': len(entries),
    'unsafe_violations': len(violations),
    'cross_target_references': len(cross_refs),
    'targets_with_spec_refs': len(spec_refs),
    'clean_full_build_exit': cp.returncode,
}, sort_keys=True))

ok = cp.returncode == 0 and not violations and not cross_refs and len(entries) >= 48
raise SystemExit(0 if ok else 1)
