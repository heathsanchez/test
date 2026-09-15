from pathlib import Path

# Diagnostic only: measure how much exact short-range locality a tiny
# direct-mapped front cache could capture before the four hottest general hash
# tables. Production hash maps remain authoritative; no result is reused by the
# diagnostic arrays.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
insert=const_marker+"""
pub(crate) const HC_DIAG_1K: usize = 1 << 10;
pub(crate) const HC_DIAG_4K: usize = 1 << 12;
"""
assert const_marker in s
s=s.replace(const_marker,insert,1)

field_marker="    pub(crate) content_hc: FxHashMap<(u8, u64), V<'a>>,\n"
fields=field_marker+"""    pub(crate) diag_canon_1k: Box<[Option<usize>; HC_DIAG_1K]>,
    pub(crate) diag_canon_4k: Box<[Option<usize>; HC_DIAG_4K]>,
    pub(crate) diag_spine_1k: Box<[Option<(usize, u64)>; HC_DIAG_1K]>,
    pub(crate) diag_spine_4k: Box<[Option<(usize, u64)>; HC_DIAG_4K]>,
    pub(crate) diag_rigid_1k: Box<[Option<(u8, u64, u64, usize)>; HC_DIAG_1K]>,
    pub(crate) diag_rigid_4k: Box<[Option<(u8, u64, u64, usize)>; HC_DIAG_4K]>,
    pub(crate) diag_unfold_1k: Box<[Option<(usize, usize)>; HC_DIAG_1K]>,
    pub(crate) diag_unfold_4k: Box<[Option<(usize, usize)>; HC_DIAG_4K]>,
"""
assert field_marker in s
s=s.replace(field_marker,fields,1)

init_marker="            content_hc: session_small_fx_hash_map(),\n"
init=init_marker+"""            diag_canon_1k: Box::new([None; HC_DIAG_1K]),
            diag_canon_4k: Box::new([None; HC_DIAG_4K]),
            diag_spine_1k: Box::new([None; HC_DIAG_1K]),
            diag_spine_4k: Box::new([None; HC_DIAG_4K]),
            diag_rigid_1k: Box::new([None; HC_DIAG_1K]),
            diag_rigid_4k: Box::new([None; HC_DIAG_4K]),
            diag_unfold_1k: Box::new([None; HC_DIAG_1K]),
            diag_unfold_4k: Box::new([None; HC_DIAG_4K]),
"""
assert init_marker in s
s=s.replace(init_marker,init,1)

clear_marker="        self.content_hc.clear();\n"
clear=clear_marker+"""        self.diag_canon_1k.fill(None);
        self.diag_canon_4k.fill(None);
        self.diag_spine_1k.fill(None);
        self.diag_spine_4k.fill(None);
        self.diag_rigid_1k.fill(None);
        self.diag_rigid_4k.fill(None);
        self.diag_unfold_1k.fill(None);
        self.diag_unfold_4k.fill(None);
"""
assert clear_marker in s
s=s.replace(clear_marker,clear,1)

session_marker="        shrink_map(&mut self.content_hc);\n"
session=session_marker+"""        self.diag_canon_1k.fill(None);
        self.diag_canon_4k.fill(None);
        self.diag_spine_1k.fill(None);
        self.diag_spine_4k.fill(None);
        self.diag_rigid_1k.fill(None);
        self.diag_rigid_4k.fill(None);
        self.diag_unfold_1k.fill(None);
        self.diag_unfold_4k.fill(None);
"""
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
static HCD_CANON_TOTAL: AtomicU64 = AtomicU64::new(0);
static HCD_CANON_MAP_HIT: AtomicU64 = AtomicU64::new(0);
static HCD_CANON_MAP_MISS: AtomicU64 = AtomicU64::new(0);
static HCD_CANON_DM1: AtomicU64 = AtomicU64::new(0);
static HCD_CANON_DM4: AtomicU64 = AtomicU64::new(0);

static HCD_SPINE_TOTAL: AtomicU64 = AtomicU64::new(0);
static HCD_SPINE_MAP_HIT: AtomicU64 = AtomicU64::new(0);
static HCD_SPINE_MAP_MISS: AtomicU64 = AtomicU64::new(0);
static HCD_SPINE_DM1: AtomicU64 = AtomicU64::new(0);
static HCD_SPINE_DM4: AtomicU64 = AtomicU64::new(0);

static HCD_RIGID_TOTAL: AtomicU64 = AtomicU64::new(0);
static HCD_RIGID_MAP_HIT: AtomicU64 = AtomicU64::new(0);
static HCD_RIGID_MAP_MISS: AtomicU64 = AtomicU64::new(0);
static HCD_RIGID_DM1: AtomicU64 = AtomicU64::new(0);
static HCD_RIGID_DM4: AtomicU64 = AtomicU64::new(0);

static HCD_UNFOLD_TOTAL: AtomicU64 = AtomicU64::new(0);
static HCD_UNFOLD_MAP_HIT: AtomicU64 = AtomicU64::new(0);
static HCD_UNFOLD_MAP_MISS: AtomicU64 = AtomicU64::new(0);
static HCD_UNFOLD_DM1: AtomicU64 = AtomicU64::new(0);
static HCD_UNFOLD_DM4: AtomicU64 = AtomicU64::new(0);

#[inline]
fn hc_diag_mix2(a: u64, b: u64) -> u64 {
    a.wrapping_mul(0x9E3779B97F4A7C15)
        .rotate_left(23)
        ^ b.wrapping_mul(0xBF58476D1CE4E5B9)
}

pub fn print_hc_front_diag() {
    eprintln!(
        "HC_FRONT_CANON total={} map_hit={} map_miss={} dm1={} dm4={}",
        HCD_CANON_TOTAL.load(Relaxed), HCD_CANON_MAP_HIT.load(Relaxed),
        HCD_CANON_MAP_MISS.load(Relaxed), HCD_CANON_DM1.load(Relaxed),
        HCD_CANON_DM4.load(Relaxed),
    );
    eprintln!(
        "HC_FRONT_SPINE total={} map_hit={} map_miss={} dm1={} dm4={}",
        HCD_SPINE_TOTAL.load(Relaxed), HCD_SPINE_MAP_HIT.load(Relaxed),
        HCD_SPINE_MAP_MISS.load(Relaxed), HCD_SPINE_DM1.load(Relaxed),
        HCD_SPINE_DM4.load(Relaxed),
    );
    eprintln!(
        "HC_FRONT_RIGID total={} map_hit={} map_miss={} dm1={} dm4={}",
        HCD_RIGID_TOTAL.load(Relaxed), HCD_RIGID_MAP_HIT.load(Relaxed),
        HCD_RIGID_MAP_MISS.load(Relaxed), HCD_RIGID_DM1.load(Relaxed),
        HCD_RIGID_DM4.load(Relaxed),
    );
    eprintln!(
        "HC_FRONT_UNFOLD total={} map_hit={} map_miss={} dm1={} dm4={}",
        HCD_UNFOLD_TOTAL.load(Relaxed), HCD_UNFOLD_MAP_HIT.load(Relaxed),
        HCD_UNFOLD_MAP_MISS.load(Relaxed), HCD_UNFOLD_DM1.load(Relaxed),
        HCD_UNFOLD_DM4.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,stats,1)

# unfold hash-cons
old="""        let key = (head_value as *const OnceCell<V<'t>> as usize, spine as *const Spine<'t> as usize);
        if let Some(u) = self.tc_cache.unfold_hc.get(&key) {
            return u;
        }
        let u = value::mk_unfold(self.arena, name, levels, spine, head_value);
"""
new="""        let key = (head_value as *const OnceCell<V<'t>> as usize, spine as *const Spine<'t> as usize);
        HCD_UNFOLD_TOTAL.fetch_add(1, Relaxed);
        let h = hc_diag_mix2(key.0 as u64, key.1 as u64);
        let i1 = h as usize & (crate::util::HC_DIAG_1K - 1);
        let i4 = h as usize & (crate::util::HC_DIAG_4K - 1);
        if self.tc_cache.diag_unfold_1k[i1] == Some(key) { HCD_UNFOLD_DM1.fetch_add(1, Relaxed); }
        if self.tc_cache.diag_unfold_4k[i4] == Some(key) { HCD_UNFOLD_DM4.fetch_add(1, Relaxed); }
        self.tc_cache.diag_unfold_1k[i1] = Some(key);
        self.tc_cache.diag_unfold_4k[i4] = Some(key);
        if let Some(u) = self.tc_cache.unfold_hc.get(&key) {
            HCD_UNFOLD_MAP_HIT.fetch_add(1, Relaxed);
            return u;
        }
        HCD_UNFOLD_MAP_MISS.fetch_add(1, Relaxed);
        let u = value::mk_unfold(self.arena, name, levels, spine, head_value);
"""
assert old in s
s=s.replace(old,new,1)

# spine hash-cons
old="""        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        let arena = self.arena;
        match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => *o.get(),
            Entry::Vacant(slot) => {
"""
new="""        let key = (prev as *const Spine<'t> as usize, elim_key(&elim));
        HCD_SPINE_TOTAL.fetch_add(1, Relaxed);
        let h = hc_diag_mix2(key.0 as u64, key.1);
        let i1 = h as usize & (crate::util::HC_DIAG_1K - 1);
        let i4 = h as usize & (crate::util::HC_DIAG_4K - 1);
        if self.tc_cache.diag_spine_1k[i1] == Some(key) { HCD_SPINE_DM1.fetch_add(1, Relaxed); }
        if self.tc_cache.diag_spine_4k[i4] == Some(key) { HCD_SPINE_DM4.fetch_add(1, Relaxed); }
        self.tc_cache.diag_spine_1k[i1] = Some(key);
        self.tc_cache.diag_spine_4k[i4] = Some(key);
        let arena = self.arena;
        match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => {
                HCD_SPINE_MAP_HIT.fetch_add(1, Relaxed);
                *o.get()
            }
            Entry::Vacant(slot) => {
                HCD_SPINE_MAP_MISS.fetch_add(1, Relaxed);
"""
assert old in s
s=s.replace(old,new,1)

# rigid hash-cons
old="""        let hk = rigid_head_key(&head);
        let key = (hk.0, hk.1, hk.2, spine as *const Spine<'t> as usize);
        let arena = self.arena;
        match self.tc_cache.rigid_hc.entry(key) {
            Entry::Occupied(o) => *o.get(),
            Entry::Vacant(slot) => {
"""
new="""        let hk = rigid_head_key(&head);
        let key = (hk.0, hk.1, hk.2, spine as *const Spine<'t> as usize);
        HCD_RIGID_TOTAL.fetch_add(1, Relaxed);
        let h = hc_diag_mix2(
            hc_diag_mix2(u64::from(key.0), key.1),
            hc_diag_mix2(key.2, key.3 as u64),
        );
        let i1 = h as usize & (crate::util::HC_DIAG_1K - 1);
        let i4 = h as usize & (crate::util::HC_DIAG_4K - 1);
        if self.tc_cache.diag_rigid_1k[i1] == Some(key) { HCD_RIGID_DM1.fetch_add(1, Relaxed); }
        if self.tc_cache.diag_rigid_4k[i4] == Some(key) { HCD_RIGID_DM4.fetch_add(1, Relaxed); }
        self.tc_cache.diag_rigid_1k[i1] = Some(key);
        self.tc_cache.diag_rigid_4k[i4] = Some(key);
        let arena = self.arena;
        match self.tc_cache.rigid_hc.entry(key) {
            Entry::Occupied(o) => {
                HCD_RIGID_MAP_HIT.fetch_add(1, Relaxed);
                *o.get()
            }
            Entry::Vacant(slot) => {
                HCD_RIGID_MAP_MISS.fetch_add(1, Relaxed);
"""
assert old in s
s=s.replace(old,new,1)

# canonical representative cache
old="""        let key = v as *const Value<'t> as usize;
        if let Some(c) = self.tc_cache.canon_cache.get(&key) {
            return c;
        }
        let c = self.canon_compute(v);
"""
new="""        let key = v as *const Value<'t> as usize;
        HCD_CANON_TOTAL.fetch_add(1, Relaxed);
        let h = (key as u64).wrapping_mul(0x9E3779B97F4A7C15).rotate_left(17);
        let i1 = h as usize & (crate::util::HC_DIAG_1K - 1);
        let i4 = h as usize & (crate::util::HC_DIAG_4K - 1);
        if self.tc_cache.diag_canon_1k[i1] == Some(key) { HCD_CANON_DM1.fetch_add(1, Relaxed); }
        if self.tc_cache.diag_canon_4k[i4] == Some(key) { HCD_CANON_DM4.fetch_add(1, Relaxed); }
        self.tc_cache.diag_canon_1k[i1] = Some(key);
        self.tc_cache.diag_canon_4k[i4] = Some(key);
        if let Some(c) = self.tc_cache.canon_cache.get(&key) {
            HCD_CANON_MAP_HIT.fetch_add(1, Relaxed);
            return c;
        }
        HCD_CANON_MAP_MISS.fetch_add(1, Relaxed);
        let c = self.canon_compute(v);
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
new="""    if std::env::var_os("SOKONANODA_HC_FRONT_DIAG").is_some() {
        sokonanoda::eval::print_hc_front_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
