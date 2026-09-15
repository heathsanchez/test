from pathlib import Path
import runpy

# Diagnostic-only: start from the exact V7 recompute ablation so every valid
# closed reuse opportunity is deliberately recomputed. Count eval() calls
# incurred by that recomputation. No production decision is changed.
runpy.run_path("scripts/patch_cq_pi_recurrence_seed_ablation.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static RC_EVAL_CALLS: AtomicU64 = AtomicU64::new(0);
static RC_MATCHES: AtomicU64 = AtomicU64::new(0);
static RC_RECOMPUTE_CALLS: AtomicU64 = AtomicU64::new(0);
static RC_MAX_CALLS: AtomicU64 = AtomicU64::new(0);
static RC_B1: AtomicU64 = AtomicU64::new(0);
static RC_B2_4: AtomicU64 = AtomicU64::new(0);
static RC_B5_16: AtomicU64 = AtomicU64::new(0);
static RC_B17_64: AtomicU64 = AtomicU64::new(0);
static RC_B65_256: AtomicU64 = AtomicU64::new(0);
static RC_B257P: AtomicU64 = AtomicU64::new(0);

#[inline]
fn record_recompute_cost(cost: u64) {
    RC_MATCHES.fetch_add(1, Relaxed);
    RC_RECOMPUTE_CALLS.fetch_add(cost, Relaxed);
    RC_MAX_CALLS.fetch_max(cost, Relaxed);
    match cost {
        0 | 1 => { RC_B1.fetch_add(1, Relaxed); }
        2..=4 => { RC_B2_4.fetch_add(1, Relaxed); }
        5..=16 => { RC_B5_16.fetch_add(1, Relaxed); }
        17..=64 => { RC_B17_64.fetch_add(1, Relaxed); }
        65..=256 => { RC_B65_256.fetch_add(1, Relaxed); }
        _ => { RC_B257P.fetch_add(1, Relaxed); }
    }
}

pub fn print_v7_reuse_cost_diag() {
    eprintln!(
        "V7_REUSE_COST matches={} recompute_eval_calls={} max_eval_calls={} b1={} b2_4={} b5_16={} b17_64={} b65_256={} b257p={}",
        RC_MATCHES.load(Relaxed),
        RC_RECOMPUTE_CALLS.load(Relaxed),
        RC_MAX_CALLS.load(Relaxed),
        RC_B1.load(Relaxed),
        RC_B2_4.load(Relaxed),
        RC_B5_16.load(Relaxed),
        RC_B17_64.load(Relaxed),
        RC_B65_256.load(Relaxed),
        RC_B257P.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""    pub(crate) fn eval(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {
        if e.is_closed() {
"""
new="""    pub(crate) fn eval(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {
        RC_EVAL_CALLS.fetch_add(1, Relaxed);
        if e.is_closed() {
"""
assert old in s
s=s.replace(old,new,1)

old="""            if let Some((binder_name, binder_style, binder_type, body)) = pi_data {
                let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
"""
new="""            if let Some((binder_name, binder_style, binder_type, body)) = pi_data {
                let mut diag_closed_before: Option<u64> = None;
                let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
"""
assert old in s
s=s.replace(old,new,1)

old="""                        if closed {
                            let _cached_domain = std::hint::black_box(domain);
                        }
"""
new="""                        if closed {
                            let _cached_domain = std::hint::black_box(domain);
                            diag_closed_before = Some(RC_EVAL_CALLS.load(Relaxed));
                        }
"""
assert old in s
s=s.replace(old,new,1)

old="""                let domain = self.eval(depth, te, binder_type);
                let ce = self.key_env(te, e);
"""
new="""                let domain = self.eval(depth, te, binder_type);
                if let Some(before) = diag_closed_before {
                    let after = RC_EVAL_CALLS.load(Relaxed);
                    record_recompute_cost(after.saturating_sub(before));
                }
                let ce = self.key_env(te, e);
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
new="""    if std::env::var_os("SOKONANODA_V7_REUSE_COST_DIAG").is_some() {
        sokonanoda::eval::print_v7_reuse_cost_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
