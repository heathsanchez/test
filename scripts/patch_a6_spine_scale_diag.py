from pathlib import Path

# Diagnostic only: measure authoritative baseline spine_hc scale.
# Does not alter lookup or return behavior.

p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
stats=marker+"""
static SS_TOTAL: AtomicU64 = AtomicU64::new(0);
static SS_HIT: AtomicU64 = AtomicU64::new(0);
static SS_MISS: AtomicU64 = AtomicU64::new(0);
static SS_PEAK: AtomicU64 = AtomicU64::new(0);

#[inline]
fn update_spine_scale_peak(n: u64) {
    let mut cur = SS_PEAK.load(Relaxed);
    while n > cur {
        match SS_PEAK.compare_exchange_weak(cur, n, Relaxed, Relaxed) {
            Ok(_) => break,
            Err(v) => cur = v,
        }
    }
}

pub fn print_spine_scale_diag() {
    eprintln!(
        "SPINE_SCALE total={} hit={} miss={} peak_len={}",
        SS_TOTAL.load(Relaxed),
        SS_HIT.load(Relaxed),
        SS_MISS.load(Relaxed),
        SS_PEAK.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,stats,1)

old="""    #[inline]
    fn spine_snoc_hc(&mut self, prev: S<'t>, elim: Elim<'t>) -> S<'t> {
        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        let arena = self.arena;
        match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => *o.get(),
            Entry::Vacant(slot) => {
                let s = value::spine_snoc(arena, prev, elim);
                let canon = prev.is_canonical()
                    && match elim.view() {
                        ElimView::App(a) => a.is_canonical(),
                        ElimView::Proj { .. } => true,
                    };
                if canon {
                    s.mark_canonical();
                }
                *slot.insert(s)
            }
        }
    }
"""
new="""    #[inline]
    fn spine_snoc_hc(&mut self, prev: S<'t>, elim: Elim<'t>) -> S<'t> {
        SS_TOTAL.fetch_add(1, Relaxed);
        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        let arena = self.arena;
        match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => {
                SS_HIT.fetch_add(1, Relaxed);
                *o.get()
            }
            Entry::Vacant(slot) => {
                SS_MISS.fetch_add(1, Relaxed);
                let s = value::spine_snoc(arena, prev, elim);
                let canon = prev.is_canonical()
                    && match elim.view() {
                        ElimView::App(a) => a.is_canonical(),
                        ElimView::Proj { .. } => true,
                    };
                if canon {
                    s.mark_canonical();
                }
                let r = *slot.insert(s);
                update_spine_scale_peak(self.tc_cache.spine_hc.len() as u64);
                r
            }
        }
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
new="""    if std::env::var_os("SOKONANODA_SPINE_SCALE_DIAG").is_some() {
        sokonanoda::eval::print_spine_scale_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
