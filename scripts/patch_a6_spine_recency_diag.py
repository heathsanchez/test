from pathlib import Path

# Diagnostic only: measure exact temporal recurrence of spine_snoc_hc keys in
# the preceding 1/2/4/8/16 calls. Production spine_hc remains authoritative.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
insert=const_marker+"pub(crate) const SPINE_RECENT_DIAG_LEN: usize = 16;\n"
assert const_marker in s
s=s.replace(const_marker,insert,1)

field_marker="    pub(crate) spine_hc: FxHashMap<(usize, u64), S<'a>>,\n"
field=field_marker+"    pub(crate) diag_spine_recent: [(usize, u64); SPINE_RECENT_DIAG_LEN],\n"
assert field_marker in s
s=s.replace(field_marker,field,1)

init_marker="            spine_hc: session_fx_hash_map(),\n"
init=init_marker+"            diag_spine_recent: [(0, 0); SPINE_RECENT_DIAG_LEN],\n"
assert init_marker in s
s=s.replace(init_marker,init,1)

clear_marker="        self.spine_hc.clear();\n"
clear=clear_marker+"        self.diag_spine_recent.fill((0, 0));\n"
assert clear_marker in s
s=s.replace(clear_marker,clear,1)

session_marker="        shrink_map(&mut self.spine_hc);\n"
session=session_marker+"        self.diag_spine_recent.fill((0, 0));\n"
assert session_marker in s
s=s.replace(session_marker,session,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
stats=marker+"""
static SR_TOTAL: AtomicU64 = AtomicU64::new(0);
static SR_MAP_HIT: AtomicU64 = AtomicU64::new(0);
static SR_MAP_MISS: AtomicU64 = AtomicU64::new(0);
static SR_LAST1: AtomicU64 = AtomicU64::new(0);
static SR_LAST2: AtomicU64 = AtomicU64::new(0);
static SR_LAST4: AtomicU64 = AtomicU64::new(0);
static SR_LAST8: AtomicU64 = AtomicU64::new(0);
static SR_LAST16: AtomicU64 = AtomicU64::new(0);

pub fn print_spine_recency_diag() {
    eprintln!(
        "SPINE_RECENCY total={} map_hit={} map_miss={} last1={} last2={} last4={} last8={} last16={}",
        SR_TOTAL.load(Relaxed),
        SR_MAP_HIT.load(Relaxed),
        SR_MAP_MISS.load(Relaxed),
        SR_LAST1.load(Relaxed),
        SR_LAST2.load(Relaxed),
        SR_LAST4.load(Relaxed),
        SR_LAST8.load(Relaxed),
        SR_LAST16.load(Relaxed),
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
        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        SR_TOTAL.fetch_add(1, Relaxed);

        let recent = &self.tc_cache.diag_spine_recent;
        if recent[0] == key { SR_LAST1.fetch_add(1, Relaxed); }
        if recent[..2].iter().any(|k| *k == key) { SR_LAST2.fetch_add(1, Relaxed); }
        if recent[..4].iter().any(|k| *k == key) { SR_LAST4.fetch_add(1, Relaxed); }
        if recent[..8].iter().any(|k| *k == key) { SR_LAST8.fetch_add(1, Relaxed); }
        if recent[..16].iter().any(|k| *k == key) { SR_LAST16.fetch_add(1, Relaxed); }
        self.tc_cache.diag_spine_recent.copy_within(0..15, 1);
        self.tc_cache.diag_spine_recent[0] = key;

        let arena = self.arena;
        match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => {
                SR_MAP_HIT.fetch_add(1, Relaxed);
                *o.get()
            }
            Entry::Vacant(slot) => {
                SR_MAP_MISS.fetch_add(1, Relaxed);
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
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p=Path("a6/src/main.rs")
s=p.read_text()
old="""    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new="""    if std::env::var_os("SOKONANODA_SPINE_RECENCY_DIAG").is_some() {
        sokonanoda::eval::print_spine_recency_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
