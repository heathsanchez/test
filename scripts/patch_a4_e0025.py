from pathlib import Path

SESSION_BUDGET=2_621_440

# Reconstruct A4 in both arms: upstream 9b4ea12 + 2.5 MiB session budget
# + E0018 transient apply_many prune removal + E0024 App open-cache bypass.
for root in ('a4','e0025'):
    p=Path(root)/'src/tc.rs'
    s=p.read_text()
    old='const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))

    p=Path(root)/'src/eval.rs'
    s=p.read_text()
    old="""                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                let pruned = self.key_env(env, body);
                env = value::env_extend(self.arena, pruned, args[i]);
                body = inner;
                i += 1;
"""
    new="""                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                env = value::env_extend(self.arena, env, args[i]);
                body = inner;
                i += 1;
"""
    assert old in s
    s=s.replace(old,new,1)

    old="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
    new="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
    assert old in s
    p.write_text(s.replace(old,new,1))

# E0025 only: starting from A4, also bypass Lambda open-eval canonicalization/cache.
p=Path('e0025/src/eval.rs')
s=p.read_text()
old="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
new="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. }
        ) {
"""
assert old in s
p.write_text(s.replace(old,new,1))
