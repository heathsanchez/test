from pathlib import Path

SESSION_BUDGET = 2_621_440

for root_name in ('a5','e0030'):
    root = Path(root_name)
    p = root / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

    p = root / 'src/eval.rs'
    s = p.read_text()
    old = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                let pruned = self.key_env(env, body);
                env = value::env_extend(self.arena, pruned, args[i]);
                body = inner;
                i += 1;
"""
    new = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                env = value::env_extend(self.arena, env, args[i]);
                body = inner;
                i += 1;
"""
    assert old in s
    s = s.replace(old, new, 1)
    old = """        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
    new = """        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. }
        ) {
"""
    assert old in s
    p.write_text(s.replace(old, new, 1))

# E0030 only: A5 no longer caches open Lambda eval, so do not pay key_env to prune
# the environment merely to construct an ordinary Lambda closure. Capturing a superset
# of the environment is semantically equivalent; this tests whether the pruning cost
# still has downstream value once Lambda cache identity has been removed.
p = Path('e0030/src/eval.rs')
s = p.read_text()
old = """            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>
                {
                let ce = self.key_env(env, e);
                value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(ce, body))
            }
"""
new = """            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>
                value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(env, body)),
"""
assert old in s
p.write_text(s.replace(old, new, 1))
