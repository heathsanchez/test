from pathlib import Path

p = Path('a5/src/eval.rs')
s = p.read_text()

# Diagnostic-only sparse sampling of eval_no_cache expression shape.
# One sample per 4096 calls keeps perturbation low and does not alter semantics.
needle = 'use std::cell::OnceCell;\n'
assert needle in s
s = s.replace(needle, needle + 'use std::sync::atomic::{AtomicU64, Ordering};\n\nstatic A5_EVAL_DIAG_CALLS: AtomicU64 = AtomicU64::new(0);\n', 1)

needle = """    fn eval_no_cache(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {
        let first = *self.ctx.read_expr_ref(e);
"""
insert = """    fn eval_no_cache(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {
        let first = *self.ctx.read_expr_ref(e);
        let diag_n = A5_EVAL_DIAG_CALLS.fetch_add(1, Ordering::Relaxed);
        if diag_n & 4095 == 0 {
            let kind = match first {
                Expr::App { .. } => "App",
                Expr::Lambda { .. } => "Lambda",
                Expr::Pi { .. } => "Pi",
                Expr::Let { .. } => "Let",
                Expr::Proj { .. } => "Proj",
                Expr::Var { .. } => "Var",
                Expr::Const { .. } => "Const",
                Expr::Sort { .. } => "Sort",
                Expr::NatLit { .. } => "NatLit",
                Expr::StringLit { .. } => "StringLit",
            };
            let mut nested_app = false;
            let mut same_fun = false;
            if let Expr::App { fun, arg, .. } = first {
                if let Expr::App { fun: f2, .. } = *self.ctx.read_expr_ref(arg) {
                    nested_app = true;
                    same_fun = fun == f2;
                }
            }
            eprintln!("A5_EVAL_SAMPLE kind={} nested_app={} same_fun={}", kind, nested_app, same_fun);
        }
"""
assert needle in s
s = s.replace(needle, insert, 1)
p.write_text(s)
