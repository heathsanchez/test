from pathlib import Path

SESSION_BUDGET=2_621_440
for root in ('a3','e0022'):
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

# E0022 only: open Let expressions showed 10,514 cache attempts and only 8 hits
# on grind-ring-5. Skip canonicalization/cache lookup for that class and evaluate directly.
p=Path('e0022/src/eval.rs'); s=p.read_text()
old="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
new="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
"""
assert old in s, 'open eval cache class match not found'
p.write_text(s.replace(old,new,1))
