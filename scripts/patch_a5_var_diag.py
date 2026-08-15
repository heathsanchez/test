from pathlib import Path

p = Path('a5/src/eval.rs')
s = p.read_text()

needle = 'use std::cell::OnceCell;\n'
assert needle in s
s = s.replace(needle, needle + 'use std::sync::atomic::{AtomicU64, Ordering};\n\nstatic A5_VAR_DIAG_CALLS: AtomicU64 = AtomicU64::new(0);\n', 1)

old = """            Expr::Var { dbj_idx, .. } => {
                let v = env.lookup(dbj_idx).expect("eval: loose bvar");
                self.force_thunk(depth, v)
            }
"""
new = """            Expr::Var { dbj_idx, .. } => {
                let n = A5_VAR_DIAG_CALLS.fetch_add(1, Ordering::Relaxed);
                if n & 1023 == 0 {
                    let env_kind = match env {
                        value::Env::Nil { .. } => "Nil",
                        value::Env::Cons { .. } => "Cons",
                        value::Env::Framed { .. } => "Framed",
                    };
                    let direct_cons0 = dbj_idx == 0 && matches!(env, value::Env::Cons { .. });
                    eprintln!("A5_VAR_SAMPLE idx={} env={} direct_cons0={}", dbj_idx, env_kind, direct_cons0);
                }
                let v = env.lookup(dbj_idx).expect("eval: loose bvar");
                self.force_thunk(depth, v)
            }
"""
assert old in s
p.write_text(s.replace(old, new, 1))
