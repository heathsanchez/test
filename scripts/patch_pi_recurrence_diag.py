from pathlib import Path

# Diagnostic only: count first vs repeated Pi expression occurrences among
# ordinary pointer-keyed open-eval cache misses.

p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)
marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static PR_PI_MISS: AtomicU64 = AtomicU64::new(0);
static PR_PI_FIRST: AtomicU64 = AtomicU64::new(0);
static PR_PI_REPEAT: AtomicU64 = AtomicU64::new(0);

pub fn print_pi_recurrence_diag() {
    eprintln!(
        "PI_RECURRENCE miss={} first={} repeat={}",
        PR_PI_MISS.load(Relaxed),
        PR_PI_FIRST.load(Relaxed),
        PR_PI_REPEAT.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }
            let v = self.eval_no_cache(depth, te, e);
"""
new="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }
            if matches!(self.ctx.read_expr_ref(e), Expr::Pi { .. }) {
                PR_PI_MISS.fetch_add(1, Relaxed);
                if self.tc_cache.open_eval_seen.insert(e) {
                    PR_PI_FIRST.fetch_add(1, Relaxed);
                } else {
                    PR_PI_REPEAT.fetch_add(1, Relaxed);
                }
            }
            let v = self.eval_no_cache(depth, te, e);
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p=Path("a6/src/main.rs")
s=p.read_text()
old="""    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new="""    if std::env::var_os("SOKONANODA_PI_RECURRENCE_DIAG").is_some() {
        sokonanoda::eval::print_pi_recurrence_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
