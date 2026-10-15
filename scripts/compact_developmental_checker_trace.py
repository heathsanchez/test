#!/usr/bin/env python3
from pathlib import Path
p=Path('trace/src/infer.rs'); s=p.read_text()
for site in ['infer.app_arg','infer.let']:
    old=f'eprintln!("[MGTRACE] kind=defeq site={site} depth={{}} ok={{}}", depth, mg_ok);'
    new=f'if !mg_ok {{ eprintln!("[MGTRACE] kind=defeq site={site} depth={{}} ok={{}}", depth, mg_ok); }}'
    if old not in s: raise SystemExit(f'compact anchor missing: {site}')
    s=s.replace(old,new,1)
p.write_text(s)
print('applied compact causal trace')
