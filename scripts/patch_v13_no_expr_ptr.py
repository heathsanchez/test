#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/run_causal_quotient_v13_cross_family.py')
s = p.read_text()

s = s.replace(
'''                eprintln!(\"[MGTRACE] kind=span_begin site=infer.app_arg_type depth={} expr={:p}\", depth, arg);\\n                let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\\n                eprintln!(\"[MGTRACE] kind=span_end site=infer.app_arg_type depth={} expr={:p} value={:p}\", depth, arg, arg_ty);''',
'''                eprintln!(\"[MGTRACE] kind=span_begin site=infer.app_arg_type depth={}\", depth);\\n                let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\\n                eprintln!(\"[MGTRACE] kind=span_end site=infer.app_arg_type depth={} value={:p}\", depth, arg_ty);''')

s = s.replace(
'''        eprintln!(\"[MGTRACE] kind=span_begin site=infer.decl_val depth=0 expr={:p}\", val);\\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\\n        eprintln!(\"[MGTRACE] kind=span_end site=infer.decl_val depth=0 expr={:p} value={:p}\", val, val_ty);''',
'''        eprintln!(\"[MGTRACE] kind=span_begin site=infer.decl_val depth=0\");\\n        let val_ty = self.infer_value(Check, 0, empty_env, empty_ctx, val);\\n        eprintln!(\"[MGTRACE] kind=span_end site=infer.decl_val depth=0 value={:p}\", val_ty);''')

old = '''    end=None; token=None\n    for i in range(fi-1,-1,-1):\n        if ev[i].get('kind')=='span_end' and ev[i].get('site')==target: end=i; token=ev[i].get('expr'); break\n    if end is None:return None\n    for i in range(end-1,-1,-1):\n        if ev[i].get('kind')=='span_begin' and ev[i].get('site')==target and ev[i].get('expr')==token:return i,end\n    return None'''
new = '''    end=None\n    for i in range(fi-1,-1,-1):\n        if ev[i].get('kind')=='span_end' and ev[i].get('site')==target:\n            end=i; break\n    if end is None:return None\n    # Structural nesting is sufficient here: take the nearest unmatched begin\n    # of the same producer-site before this completed span. No ExprPtr identity needed.\n    depth=0\n    for i in range(end-1,-1,-1):\n        if ev[i].get('site')!=target: continue\n        if ev[i].get('kind')=='span_end': depth += 1\n        elif ev[i].get('kind')=='span_begin':\n            if depth==0: return i,end\n            depth -= 1\n    return None'''
if old not in s:
    raise SystemExit('producer_span anchor missing')
s = s.replace(old, new, 1)

if 'expr={:p}' in s:
    raise SystemExit('ExprPtr pointer formatting remains')

p.write_text(s)
print('patched V13 to use structural span pairing without ExprPtr pointer formatting')
