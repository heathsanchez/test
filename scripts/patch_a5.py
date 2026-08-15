from pathlib import Path

SESSION_BUDGET = 2_621_440
root = Path('a5')

# A2 component: 2.5 MiB session budget.
p = root / 'src/tc.rs'
s = p.read_text()
old = 'const SESSION_BUDGET: usize = 1 << 20;'
assert old in s
p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

# A3 / E0018: do not canonicalize transient environments between chained lambda applications.
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

# A4 / E0024 + A5 / E0025: App and Lambda do not enter the open-eval canonicalization/cache path.
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
