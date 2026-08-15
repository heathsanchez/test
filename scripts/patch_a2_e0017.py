from pathlib import Path

SESSION_BUDGET = 2_621_440
for root in ('a2','e0017'):
    p = Path(root) / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

p = Path('e0017/src/eval.rs')
s = p.read_text()

old = """            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>
                {
                let ce = self.key_env(env, e);
                value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(ce, body))
            }
            Expr::Pi { binder_name, binder_style, binder_type, body, .. } => {
                let dom = self.eval(depth, env, binder_type);
                {
                    let ce = self.key_env(env, e);
                    value::mk_pi(self.arena, binder_name, binder_style, dom, Closure::mk_eval(ce, body))
                }
            }
"""
new = """            Expr::Lambda { binder_name, binder_style, binder_type, body, .. } =>
                {
                // For open structural expressions, eval() has already canonicalized env
                // before calling eval_no_cache. Closed expressions have no loose bvars,
                // so reduce to the level-substitution base without invoking prune_env.
                let ce = if e.num_loose_bvars() == 0 { self.lsub_base(env.lsub()) } else { env };
                value::mk_lam(self.arena, binder_name, binder_style, binder_type, Closure::mk_eval(ce, body))
            }
            Expr::Pi { binder_name, binder_style, binder_type, body, .. } => {
                let dom = self.eval(depth, env, binder_type);
                {
                    let ce = if e.num_loose_bvars() == 0 { self.lsub_base(env.lsub()) } else { env };
                    value::mk_pi(self.arena, binder_name, binder_style, dom, Closure::mk_eval(ce, body))
                }
            }
"""
assert old in s, 'eval Lambda/Pi block not found'
s = s.replace(old, new, 1)
p.write_text(s)
