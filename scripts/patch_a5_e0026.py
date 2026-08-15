from pathlib import Path

SESSION_BUDGET = 2_621_440

for root_name in ('a5','e0026'):
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

# E0026 only: unify() already force_thunk()s both values before calling unify_general().
# unify_general() is the sole caller of unify_no_cache(), so the second force_thunk pair
# at unify_no_cache entry is redundant. Reuse the already-forced values directly.
p = Path('e0026/src/conv.rs')
s = p.read_text()
old = """        let (t, t2) = (self.force_thunk(depth, x), self.force_thunk(depth, y));
        if let Some(r) = self.conv_nat::<RIGID>(depth, t, t2) {
"""
new = """        let (t, t2) = (x, y);
        if let Some(r) = self.conv_nat::<RIGID>(depth, t, t2) {
"""
assert old in s
p.write_text(s.replace(old, new, 1))
