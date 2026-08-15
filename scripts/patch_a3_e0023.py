from pathlib import Path

SESSION_BUDGET=2_621_440
for root in ('a3','e0023'):
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

# E0023 only: bypass the open-eval canonicalization/cache path for Lambda.
# A3 diagnostic on grind-ring-5 sampled Lambda as a material class with ~29.5% hits,
# ~12.8% same-env keys, mean 4.606 loose bvars and 3.196 mask-popcount.
# This tests whether cache value exceeds the cost of key_env for this lifecycle class.
p=Path('e0023/src/eval.rs'); s=p.read_text()
old="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
new="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. }
        ) {
"""
assert old in s, 'open eval cache class match not found'
p.write_text(s.replace(old,new,1))
