from pathlib import Path

SESSION_BUDGET = 2_621_440
root = Path('a6')

# A3: larger session budget.
p = root / 'src/tc.rs'
s = p.read_text()
old = 'const SESSION_BUDGET: usize = 1 << 20;'
assert old in s
p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

# A3/E0018 + A4/E0024 + A5/E0025 + A6/E0030.
p = root / 'src/eval.rs'
s = p.read_text()

# E0018: do not prune transient env while consuming nested lambdas in apply_many.
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

# E0024 + E0025: bypass open-eval cache/canonicalization for App and Lambda.
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
s = s.replace(old, new, 1)

# E0030: Lambda is no longer keyed/cached at open eval, so capture the existing
# environment directly rather than paying key_env merely to build the closure.
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
s = s.replace(old, new, 1)

p.write_text(s)
