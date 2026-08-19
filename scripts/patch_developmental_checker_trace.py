#!/usr/bin/env python3
from pathlib import Path

root = Path('trace')

# Instrument inference failure boundaries without changing control flow.
p = root / 'src' / 'infer.rs'
s = p.read_text()
repls = [
    (
        '                    let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\n                    assert!(self.conv_types_at(depth, domain, arg_ty), "app arg def_eq failed");',
        '                    let arg_ty = self.infer_value(flag, depth, env, ctx, arg);\n                    let mg_ok = self.conv_types_at(depth, domain, arg_ty);\n                    eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);\n                    assert!(mg_ok, "app arg def_eq failed");'
    ),
    (
        '                    let val_ty = self.infer_value(flag, depth, env, ctx, val);\n                    assert!(self.conv_types_at(depth, dom, val_ty), "let def_eq failed");',
        '                    let val_ty = self.infer_value(flag, depth, env, ctx, val);\n                    let mg_ok = self.conv_types_at(depth, dom, val_ty);\n                    eprintln!("[MGTRACE] kind=defeq site=infer.let depth={} ok={}", depth, mg_ok);\n                    assert!(mg_ok, "let def_eq failed");'
    ),
    (
        '        let struct_ty = self.infer_value(flag, depth, env, ctx, structure);',
        '        eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);\n        let struct_ty = self.infer_value(flag, depth, env, ctx, structure);'
    ),
]
for old, new in repls:
    if old not in s:
        raise SystemExit(f'infer anchor not found: {old[:70]!r}')
    s = s.replace(old, new, 1)
p.write_text(s)

# Instrument conversion/reduction decisions. No raw expressions or theorem names are emitted.
p = root / 'src' / 'conv.rs'
s = p.read_text()
old = '''            if self.tc_cache.probe_budget == 0 {\n                self.tc_cache.probe_exhausted = true;\n                return false;\n            }'''
new = '''            if self.tc_cache.probe_budget == 0 {\n                eprintln!("[MGTRACE] kind=resource site=conv.probe_exhausted depth={}", depth);\n                self.tc_cache.probe_exhausted = true;\n                return false;\n            }'''
if old not in s:
    raise SystemExit('probe anchor not found')
s = s.replace(old, new, 1)

old = '                self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy)'
new = '''                eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);\n                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.recursor depth={} ok={}", depth, mg_r);\n                mg_r'''
if s.count(old) < 2:
    raise SystemExit(f'expected two iota anchors, found {s.count(old)}')
s = s.replace(old, new, 1)
new2 = '''                eprintln!("[MGTRACE] kind=iota site=conv.quot depth={} heads_match={}", depth, heads_match);\n                let mg_r = self.unify_iota::<RIGID>(depth, t, t2, heads_match, nx, lx, sx, sy);\n                eprintln!("[MGTRACE] kind=iota_result site=conv.quot depth={} ok={}", depth, mg_r);\n                mg_r'''
s = s.replace(old, new2, 1)

old = '                        return self.unfold_pair(depth, t, t2);'
new = '                        eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);\n                        return self.unfold_pair(depth, t, t2);'
if old not in s:
    raise SystemExit('unfold_pair anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)

print('applied semantics-preserving developmental trace instrumentation')
