from pathlib import Path
import runpy

# Diagnostic-only V7 telemetry. Applies the frozen V7 candidate unchanged, then
# counts activation funnel events. No decision or returned value is changed.
runpy.run_path("scripts/patch_cq_pi_recurrence_seed.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static V7D_PI_MISS: AtomicU64 = AtomicU64::new(0);
static V7D_SEED_NONE: AtomicU64 = AtomicU64::new(0);
static V7D_SEED_COLLISION: AtomicU64 = AtomicU64::new(0);
static V7D_SAME_EXPR: AtomicU64 = AtomicU64::new(0);
static V7D_ENV_EQ: AtomicU64 = AtomicU64::new(0);
static V7D_CLOSED_REUSE: AtomicU64 = AtomicU64::new(0);
static V7D_OPEN_EQ: AtomicU64 = AtomicU64::new(0);

pub fn print_v7_activation_diag() {
    eprintln!(
        "V7_ACTIVATION pi_miss={} seed_none={} seed_collision={} same_expr={} env_eq={} closed_reuse={} open_eq={}",
        V7D_PI_MISS.load(Relaxed),
        V7D_SEED_NONE.load(Relaxed),
        V7D_SEED_COLLISION.load(Relaxed),
        V7D_SAME_EXPR.load(Relaxed),
        V7D_ENV_EQ.load(Relaxed),
        V7D_CLOSED_REUSE.load(Relaxed),
        V7D_OPEN_EQ.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""            if let Some((binder_name, binder_style, binder_type, body)) = pi_data {
                let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
"""
new="""            if let Some((binder_name, binder_style, binder_type, body)) = pi_data {
                V7D_PI_MISS.fetch_add(1, Relaxed);
                let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
"""
assert old in s
s=s.replace(old,new,1)

old="""                if let Some(seed) = self.tc_cache.cq_pi_seed[slot] {
                    if seed.expr == e && self.cq_seed_env_eq(te, seed.env) {
                        let domain = std::hint::black_box(seed.domain);
                        let closed = std::hint::black_box(domain.is_closed());
                        if closed {
                            let ce = self.key_env(te, e);
                            let v = value::mk_pi(
                                self.arena,
                                binder_name,
                                binder_style,
                                domain,
                                Closure::mk_eval(ce, body),
                            );
                            self.tc_cache.open_eval_cache.insert(key, v);
                            return v;
                        }
                    }
                }
"""
new="""                if let Some(seed) = self.tc_cache.cq_pi_seed[slot] {
                    if seed.expr == e {
                        V7D_SAME_EXPR.fetch_add(1, Relaxed);
                        if self.cq_seed_env_eq(te, seed.env) {
                            V7D_ENV_EQ.fetch_add(1, Relaxed);
                            let domain = std::hint::black_box(seed.domain);
                            let closed = std::hint::black_box(domain.is_closed());
                            if closed {
                                V7D_CLOSED_REUSE.fetch_add(1, Relaxed);
                                let ce = self.key_env(te, e);
                                let v = value::mk_pi(
                                    self.arena,
                                    binder_name,
                                    binder_style,
                                    domain,
                                    Closure::mk_eval(ce, body),
                                );
                                self.tc_cache.open_eval_cache.insert(key, v);
                                return v;
                            } else {
                                V7D_OPEN_EQ.fetch_add(1, Relaxed);
                            }
                        }
                    } else {
                        V7D_SEED_COLLISION.fetch_add(1, Relaxed);
                    }
                } else {
                    V7D_SEED_NONE.fetch_add(1, Relaxed);
                }
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
new="""    if std::env::var_os("SOKONANODA_V7_ACTIVATION_DIAG").is_some() {
        sokonanoda::eval::print_v7_activation_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
