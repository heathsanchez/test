from pathlib import Path

SESSION_BUDGET=2_621_440
for root in ('a3','e0024'):
    p=Path(root)/'src/tc.rs'; s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'; assert old in s; p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))
    p=Path(root)/'src/eval.rs'; s=p.read_text()
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
    assert old in s; p.write_text(s.replace(old,new,1))

# E0024 only: bypass open-eval canonicalization/cache for App.
# This is the dominant sampled open-eval class on grind-ring-5 (~69% of samples),
# with ~32.6% cache hits and only ~14.7% same-env canonical keys. The experiment
# directly tests whether the large key_env cost is repaid by those hits.
p=Path('e0024/src/eval.rs'); s=p.read_text()
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
assert old in s, 'open eval cache class match not found'
p.write_text(s.replace(old,new,1))
