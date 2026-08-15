from pathlib import Path

SESSION_BUDGET = 2_621_440
for root in ('a3','e0020'):
    p = Path(root) / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

    p = Path(root) / 'src/eval.rs'
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
    p.write_text(s.replace(old,new,1))

# E0020 only: retain the bump allocator's allocated chunks across session resets.
p = Path('e0020/src/util.rs')
s = p.read_text()
old = '    pub(crate) fn reset(&mut self) { self.inner = bumpalo::Bump::new() }'
new = '    pub(crate) fn reset(&mut self) { self.inner.reset() }'
assert old in s, 'SessionBump reset implementation not found'
p.write_text(s.replace(old,new,1))
