from pathlib import Path

p = Path('a5') / 'src' / 'conv.rs'
s = p.read_text()

# Diagnostic-only: expose conversion branch costs to Callgrind.
# This must never be treated as a performance candidate.
targets = [
    'unify_no_cache',
    'unify_direct',
    'unify_cold',
    'conv_nat',
    'unify_spine',
    'unfold_pair',
    'spine_probe',
    'try_proof_irrel_at',
    'unify_iota',
]

for name in targets:
    needles = [f'    fn {name}', f'    pub(crate) fn {name}']
    found = False
    for needle in needles:
        if needle in s:
            s = s.replace(needle, f'    #[inline(never)]\n{needle}', 1)
            found = True
            break
    if not found:
        print(f'WARN function not found: {name}')

p.write_text(s)
