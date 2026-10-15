#!/usr/bin/env python3
from pathlib import Path
import re
p=Path('scripts/run_developmental_checker_span_v8.py')
s=p.read_text()
repls={
'eprintln!("[MGTRACE] kind=span_begin site=infer.app_arg_type depth={} expr={:p}", depth, arg);':'eprintln!("[MGTRACE] kind=span_begin site=infer.app_arg_type depth={}", depth);',
'eprintln!("[MGTRACE] kind=span_end site=infer.app_arg_type depth={} expr={:p} value={:p}", depth, arg, arg_ty);':'eprintln!("[MGTRACE] kind=span_end site=infer.app_arg_type depth={} value={:p}", depth, arg_ty);',
'eprintln!("[MGTRACE] kind=span_begin site=infer.decl_val depth=0 expr={:p}", val);':'eprintln!("[MGTRACE] kind=span_begin site=infer.decl_val depth=0");',
'eprintln!("[MGTRACE] kind=span_end site=infer.decl_val depth=0 expr={:p} value={:p}", val, val_ty);':'eprintln!("[MGTRACE] kind=span_end site=infer.decl_val depth=0 value={:p}", val_ty);',
}
for a,b in repls.items():
    if a not in s: raise SystemExit(f'missing span formatting anchor: {a[:60]}')
    s=s.replace(a,b,1)
pat=re.compile(r'def producer_span\(ev, fail_idx\):\n.*?\n(?=def mechanism\(e\):)',re.S)
new='''def producer_span(ev, fail_idx):
    if fail_idx is None: return None
    f=ev[fail_idx]; site=f.get('site')
    target='infer.decl_val' if site=='infer.decl' else ('infer.app_arg_type' if site=='infer.app_arg' else None)
    if not target: return None
    end_idx=None
    for i in range(fail_idx-1,-1,-1):
        if ev[i].get('kind')=='span_end' and ev[i].get('site')==target:
            end_idx=i; break
    if end_idx is None: return None
    # Match nested spans structurally; no expression identity is emitted.
    balance=0; begin_idx=None
    for i in range(end_idx,-1,-1):
        if ev[i].get('site')!=target: continue
        if ev[i].get('kind')=='span_end': balance+=1
        elif ev[i].get('kind')=='span_begin':
            balance-=1
            if balance==0:
                begin_idx=i; break
    if begin_idx is None: return None
    return begin_idx,end_idx

'''
s,n=pat.subn(new,s,count=1)
if n!=1: raise SystemExit(f'producer_span replacement count={n}')
p.write_text(s)
print('patched V8 runner to structural span matching')
