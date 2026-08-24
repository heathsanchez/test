from pathlib import Path

p = Path('arena/_build/checkers/mathgraph/src/src/eval.rs')
s = p.read_text()

anchor = "const FAIL_DEPTH: u8 = 7;\n"
wrappers = r'''

#[inline(never)]
fn v40_diag_app<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_var<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_sort<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_const<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_lambda<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_pi<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_let<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_proj<R>(f: impl FnOnce() -> R) -> R { f() }
#[inline(never)]
fn v40_diag_literal<R>(f: impl FnOnce() -> R) -> R { f() }
'''
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + wrappers)

needle = "    fn eval_no_cache(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {"
assert s.count(needle) == 1
s = s.replace(needle, "    #[inline(never)]\n" + needle)

start = "        if let Expr::App { fun, arg, .. } = first {\n"
end = "            return self.apply(depth, f, a);\n        }\n        match first {\n"
assert s.count(start) == 1 and s.count(end) == 1
s = s.replace(start, start + "            return v40_diag_app(|| {\n", 1)
s = s.replace(end, "            self.apply(depth, f, a)\n            });\n        }\n        match first {\n", 1)

reps = {
'''            Expr::Var { dbj_idx, .. } => {\n                let v = env.lookup(dbj_idx).expect("eval: loose bvar");\n                self.force_thunk(depth, v)\n            }''': '''            Expr::Var { dbj_idx, .. } => v40_diag_var(|| {\n                let v = env.lookup(dbj_idx).expect("eval: loose bvar");\n                self.force_thunk(depth, v)\n            })''',
'''            Expr::Sort { level, .. } => {\n                let level = match env.lsub() {\n                    Some(ls) => self.ctx.subst_level(level, ls.ks, ls.vs),\n                    None => level,\n                };\n                value::mk_sort(self.arena, self.ctx.simplify(level))\n            }''': '''            Expr::Sort { level, .. } => v40_diag_sort(|| {\n                let level = match env.lsub() {\n                    Some(ls) => self.ctx.subst_level(level, ls.ks, ls.vs),\n                    None => level,\n                };\n                value::mk_sort(self.arena, self.ctx.simplify(level))\n            })''',
'''            Expr::Const { name, levels, .. } => {\n                let levels = match env.lsub() {\n                    Some(ls) => self.ctx.subst_levels(levels, ls.ks, ls.vs),\n                    None => levels,\n                };\n                self.eval_const(name, levels)\n            }''': '''            Expr::Const { name, levels, .. } => v40_diag_const(|| {\n                let levels = match env.lsub() {\n                    Some(ls) => self.ctx.subst_levels(levels, ls.ks, ls.vs),\n                    None => levels,\n                };\n                self.eval_const(name, levels)\n            })''',
'''            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>\n                value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(env, body)),''': '''            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>\n                v40_diag_lambda(|| value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(env, body))),''',
'''            Expr::Pi { binder_name, binder_style, binder_type, body, .. } => {\n                let dom = match self.ctx.read_expr_ref(binder_type) {\n                    Expr::Var { .. }\n                    | Expr::Sort { .. }\n                    | Expr::Const { .. }\n                    | Expr::NatLit { .. }\n                    | Expr::StringLit { .. } => self.eval(depth, env, binder_type),\n                    _ => self.mk_thunk_hc(env, binder_type),\n                };\n                value::mk_pi(self.arena, binder_name, binder_style, dom, Closure::mk_eval(env, body))\n            }''': '''            Expr::Pi { binder_name, binder_style, binder_type, body, .. } => v40_diag_pi(|| {\n                let dom = match self.ctx.read_expr_ref(binder_type) {\n                    Expr::Var { .. }\n                    | Expr::Sort { .. }\n                    | Expr::Const { .. }\n                    | Expr::NatLit { .. }\n                    | Expr::StringLit { .. } => self.eval(depth, env, binder_type),\n                    _ => self.mk_thunk_hc(env, binder_type),\n                };\n                value::mk_pi(self.arena, binder_name, binder_style, dom, Closure::mk_eval(env, body))\n            })''',
'''            Expr::Let { .. } => {\n                let mut env = env;\n                let mut cursor = e;\n                while let Expr::Let { data: &crate::expr::LetData { val, body, .. }, .. } = self.ctx.read_expr(cursor) {\n                    let vv = self.eval(depth, env, val);\n                    env = value::env_extend(self.arena, env, vv);\n                    cursor = body;\n                }\n                self.eval(depth, env, cursor)\n            }''': '''            Expr::Let { .. } => v40_diag_let(|| {\n                let mut env = env;\n                let mut cursor = e;\n                while let Expr::Let { data: &crate::expr::LetData { val, body, .. }, .. } = self.ctx.read_expr(cursor) {\n                    let vv = self.eval(depth, env, val);\n                    env = value::env_extend(self.arena, env, vv);\n                    cursor = body;\n                }\n                self.eval(depth, env, cursor)\n            })''',
'''            Expr::Proj { ty_name, idx, structure, .. } => {\n                let vs = self.eval(depth, env, structure);\n                self.do_proj(depth, ty_name, idx, vs)\n            }''': '''            Expr::Proj { ty_name, idx, structure, .. } => v40_diag_proj(|| {\n                let vs = self.eval(depth, env, structure);\n                self.do_proj(depth, ty_name, idx, vs)\n            })''',
'''            Expr::NatLit { ptr, .. } => value::mk_natlit(self.arena, ptr),\n            Expr::StringLit { ptr, .. } => value::mk_strlit(self.arena, ptr),''': '''            Expr::NatLit { ptr, .. } => v40_diag_literal(|| value::mk_natlit(self.arena, ptr)),\n            Expr::StringLit { ptr, .. } => v40_diag_literal(|| value::mk_strlit(self.arena, ptr)),'''
}
for a, b in reps.items():
    if s.count(a) != 1:
        raise SystemExit(f'PATCH_MISS count={s.count(a)} fragment={a[:80]!r}')
    s = s.replace(a, b, 1)

p.write_text(s)
print('V40 patch applied: explicit noinline case boundaries; semantics intended unchanged')
