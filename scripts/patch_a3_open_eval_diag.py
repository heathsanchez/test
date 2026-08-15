from pathlib import Path
p=Path('a3/src/eval.rs')
s=p.read_text()
needle='use std::collections::hash_map::Entry;\n'
assert needle in s
s=s.replace(needle, needle+'use std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nstatic OPEN_EVAL_SAMPLE: AtomicU64 = AtomicU64::new(0);\n',1)
old='''        if matches!(\n            self.ctx.read_expr_ref(e),\n            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }\n        ) {\n            let te = self.key_env(env, e);\n            let key = (te as *const value::Env<'t> as usize, e);\n            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {\n                return v;\n            }\n            let v = self.eval_no_cache(depth, te, e);\n'''
new='''        if matches!(\n            self.ctx.read_expr_ref(e),\n            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }\n        ) {\n            let kind = match self.ctx.read_expr_ref(e) {\n                Expr::App { .. } => "App",\n                Expr::Proj { .. } => "Proj",\n                Expr::Let { .. } => "Let",\n                Expr::Pi { .. } => "Pi",\n                Expr::Lambda { .. } => "Lambda",\n                _ => unreachable!(),\n            };\n            let te = self.key_env(env, e);\n            let key = (te as *const value::Env<'t> as usize, e);\n            let hit = self.tc_cache.open_eval_cache.get(&key).copied();\n            let sample = OPEN_EVAL_SAMPLE.fetch_add(1, Relaxed);\n            if sample & 1023 == 0 {\n                eprintln!("OPEN_EVAL kind={} hit={} sameenv={} loose={} maskpop={}", kind, hit.is_some(), std::ptr::eq(te, env), e.num_loose_bvars(), e.as_ref().fv_mask().count_ones());\n            }\n            if let Some(v) = hit {\n                return v;\n            }\n            let v = self.eval_no_cache(depth, te, e);\n'''
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
