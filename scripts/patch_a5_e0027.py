from pathlib import Path

SESSION_BUDGET = 2_621_440

for root_name in ('a5','e0027'):
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

# E0027 only: fuse the two traversals of right-nested App chains.
# A5 first scans the chain to determine all_same/count, then scans it again to build `funs`
# whenever all_same is false. Diagnostics found 141/484 sampled Apps nested and 0/141
# nested samples all-same, so the second traversal is normally pure overhead on the hot path.
p = Path('e0027/src/eval.rs')
s = p.read_text()
old1 = """                let first_fun = fun;
                let mut all_same = fun == f2;
                let mut count = 2u32;
                let mut cur = a2;
                let leaf_expr;
                loop {
                    match self.ctx.read_expr_ref(cur) {
                        &Expr::App { fun: fn3, arg: an3, .. } => {
                            count += 1;
                            if all_same && fn3 != first_fun {
                                all_same = false;
                            }
                            cur = an3;
                        }
                        _ => {
                            leaf_expr = cur;
                            break;
                        }
                    }
                }
"""
new1 = """                let first_fun = fun;
                let mut all_same = fun == f2;
                let mut funs: Vec<ExprPtr<'t>> = Vec::with_capacity(4);
                funs.push(fun);
                funs.push(f2);
                let mut cur = a2;
                let leaf_expr;
                loop {
                    match self.ctx.read_expr_ref(cur) {
                        &Expr::App { fun: fn3, arg: an3, .. } => {
                            funs.push(fn3);
                            if all_same && fn3 != first_fun {
                                all_same = false;
                            }
                            cur = an3;
                        }
                        _ => {
                            leaf_expr = cur;
                            break;
                        }
                    }
                }
                let count = funs.len() as u32;
"""
assert old1 in s
s = s.replace(old1, new1, 1)
old2 = """                let mut funs: Vec<ExprPtr<'t>> = Vec::with_capacity(count as usize);
                funs.push(fun);
                funs.push(f2);
                let mut cur2 = a2;
                while let &Expr::App { fun: fn3, arg: an3, .. } = self.ctx.read_expr_ref(cur2) {
                    funs.push(fn3);
                    cur2 = an3;
                }
"""
assert old2 in s
s = s.replace(old2, '', 1)
p.write_text(s)
