from pathlib import Path

SESSION_BUDGET = 2_621_440

for root_name in ('a5','e0029'):
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

# E0029 only: specialize the dominant local de Bruijn lookups when the environment prefix is Cons.
# Diagnostic: idx 0..3 = 1485/2095 = 70.9% of sampled Var calls; Cons = 1950/2095 = 93.1%.
p = Path('e0029/src/eval.rs')
s = p.read_text()
old = """            Expr::Var { dbj_idx, .. } => {
                let v = env.lookup(dbj_idx).expect("eval: loose bvar");
                self.force_thunk(depth, v)
            }
"""
new = """            Expr::Var { dbj_idx, .. } => {
                let fast = match dbj_idx {
                    0 => match env {
                        value::Env::Cons { v, .. } => Some(*v),
                        _ => None,
                    },
                    1 => match env {
                        value::Env::Cons { parent, .. } => match *parent {
                            value::Env::Cons { v, .. } => Some(*v),
                            _ => None,
                        },
                        _ => None,
                    },
                    2 => match env {
                        value::Env::Cons { parent, .. } => match *parent {
                            value::Env::Cons { parent, .. } => match *parent {
                                value::Env::Cons { v, .. } => Some(*v),
                                _ => None,
                            },
                            _ => None,
                        },
                        _ => None,
                    },
                    3 => match env {
                        value::Env::Cons { parent, .. } => match *parent {
                            value::Env::Cons { parent, .. } => match *parent {
                                value::Env::Cons { parent, .. } => match *parent {
                                    value::Env::Cons { v, .. } => Some(*v),
                                    _ => None,
                                },
                                _ => None,
                            },
                            _ => None,
                        },
                        _ => None,
                    },
                    _ => None,
                };
                let v = fast.unwrap_or_else(|| env.lookup(dbj_idx).expect("eval: loose bvar"));
                self.force_thunk(depth, v)
            }
"""
assert old in s
p.write_text(s.replace(old, new, 1))
