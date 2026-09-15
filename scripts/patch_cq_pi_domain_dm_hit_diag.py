from pathlib import Path
import runpy

# Apply the exact V5 candidate, then add diagnostic-only hit classification.
runpy.run_path("scripts/patch_cq_pi_domain_dm.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static DMH_TOTAL: AtomicU64 = AtomicU64::new(0);
static DMH_CLOSED: AtomicU64 = AtomicU64::new(0);
static DMH_CANON: AtomicU64 = AtomicU64::new(0);
static DMH_LAM: AtomicU64 = AtomicU64::new(0);
static DMH_PI: AtomicU64 = AtomicU64::new(0);
static DMH_SORT: AtomicU64 = AtomicU64::new(0);
static DMH_NAT: AtomicU64 = AtomicU64::new(0);
static DMH_STR: AtomicU64 = AtomicU64::new(0);
static DMH_RIGID: AtomicU64 = AtomicU64::new(0);
static DMH_UNFOLD: AtomicU64 = AtomicU64::new(0);
static DMH_THUNK: AtomicU64 = AtomicU64::new(0);

#[inline]
fn cq_dm_diag_hit(v: V<'_>) {
    DMH_TOTAL.fetch_add(1, Relaxed);
    if v.is_canonical() {
        DMH_CANON.fetch_add(1, Relaxed);
    }
    if v.is_closed() {
        DMH_CLOSED.fetch_add(1, Relaxed);
    }
    match v {
        Value::Lam { .. } => { DMH_LAM.fetch_add(1, Relaxed); }
        Value::Pi { .. } => { DMH_PI.fetch_add(1, Relaxed); }
        Value::Sort { .. } => { DMH_SORT.fetch_add(1, Relaxed); }
        Value::NatLit { .. } => { DMH_NAT.fetch_add(1, Relaxed); }
        Value::StrLit { .. } => { DMH_STR.fetch_add(1, Relaxed); }
        Value::Rigid { .. } => { DMH_RIGID.fetch_add(1, Relaxed); }
        Value::Unfold { .. } => { DMH_UNFOLD.fetch_add(1, Relaxed); }
        Value::Thunk { .. } => { DMH_THUNK.fetch_add(1, Relaxed); }
    }
}

pub fn print_cq_dm_hit_diag() {
    eprintln!(
        "CQ_DM_HIT total={} closed={} canonical={} lam={} pi={} sort={} nat={} str={} rigid={} unfold={} thunk={}",
        DMH_TOTAL.load(Relaxed),
        DMH_CLOSED.load(Relaxed),
        DMH_CANON.load(Relaxed),
        DMH_LAM.load(Relaxed),
        DMH_PI.load(Relaxed),
        DMH_SORT.load(Relaxed),
        DMH_NAT.load(Relaxed),
        DMH_STR.load(Relaxed),
        DMH_RIGID.load(Relaxed),
        DMH_UNFOLD.load(Relaxed),
        DMH_THUNK.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""                    if let Some(domain) = hit {
                        let domain = std::hint::black_box(domain);
                        let ce = self.key_env(te, e);
"""
new="""                    if let Some(domain) = hit {
                        let domain = std::hint::black_box(domain);
                        cq_dm_diag_hit(domain);
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
new="""    if std::env::var_os("SOKONANODA_CQ_DM_HIT_DIAG").is_some() {
        sokonanoda::eval::print_cq_dm_hit_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
