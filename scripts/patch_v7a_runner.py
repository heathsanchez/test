#!/usr/bin/env python3
from pathlib import Path
import re

p=Path('scripts/run_developmental_checker_provenance_v7.py')
s=p.read_text()

# Extend the semantics-preserving provenance instrumentation to the declaration-level
# defeq boundary that V7 revealed as the actual downstream consumer for projection faults.
needle="""    p.write_text(s)\n\ndef natural_family(ev):"""
inject="""    old_decl='        assert!(self.def_eq_at(0, val_ty, declared), \\\"def_eq failed\\\");'\n    new_decl='        let mg_decl_ok = self.def_eq_at(0, val_ty, declared);\\n        eprintln!(\\\"[MGTRACE] kind=defeq site=infer.decl depth=0 ok={} val={:p} declared={:p}\\\", mg_decl_ok, val_ty, declared);\\n        assert!(mg_decl_ok, \\\"def_eq failed\\\");'\n    if old_decl not in s: raise RuntimeError('declaration defeq anchor missing')\n    s=s.replace(old_decl,new_decl,1)\n    p.write_text(s)\n\ndef natural_family(ev):"""
if needle not in s:
    raise SystemExit('augment_provenance insertion point not found')
s=s.replace(needle,inject,1)

pat=re.compile(r"def route_provenance\(ev\):\n.*?\n(?=def inject_fault\(src,fam\):)",re.S)
new='''def route_provenance(ev):
    # Start from the latest failed defeq consumer, whether inside application
    # inference or at the declaration admission boundary.
    failed_idx=None; consumer=None
    for idx in range(len(ev)-1,-1,-1):
        e=ev[idx]
        if e.get('kind')!='defeq' or e.get('ok')!='false': continue
        if e.get('site')=='infer.app_arg':
            failed_idx=idx; consumer=e.get('arg'); break
        if e.get('site')=='infer.decl':
            failed_idx=idx; consumer=e.get('val'); break
    if failed_idx is not None and consumer:
        for e in reversed(ev[:failed_idx]):
            if e.get('kind')=='projection_result' and e.get('value')==consumer:
                return 'PROJECTION'
    # Boolean mechanisms expose their own negative result.
    for e in reversed(ev):
        if e.get('kind')=='iota_result' and e.get('ok')=='false': return 'IOTA'
    return None

'''
s2,n=pat.subn(new,s,count=1)
if n!=1:
    raise SystemExit(f'route_provenance replacement count={n}')
p.write_text(s2)
print('patched V7 runner for declaration-consumer provenance')
