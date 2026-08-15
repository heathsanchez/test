from pathlib import Path

SESSION_BUDGET = 2_621_440
for root in ('a2','e0018'):
    p = Path(root) / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

p = Path('e0018/src/eval.rs')
s = p.read_text()
old = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                let pruned = self.key_env(env, body);
                env = value::env_extend(self.arena, pruned, args[i]);
                body = inner;
                i += 1;
"""
new = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                // This environment is transient within apply_many. Preserve the full
                // semantically equivalent environment here and let the normal downstream
                // eval/persistence boundary canonicalize when needed.
                env = value::env_extend(self.arena, env, args[i]);
                body = inner;
                i += 1;
"""
assert old in s, 'apply_many nested-lambda prune block not found'
s = s.replace(old, new, 1)
p.write_text(s)
