from pathlib import Path

# Diagnostic only. Assumes `a6` was reconstructed with scripts/patch_a6.py.
p = Path('a6/src/eval.rs')
s = p.read_text()

s = s.replace(
    'use std::cell::OnceCell;\n',
    'use std::cell::OnceCell;\nuse std::collections::HashSet;\nuse std::sync::{LazyLock, Mutex};\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n',
    1,
)

marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + r'''

static E0031_COLD_CALLS: AtomicU64 = AtomicU64::new(0);
static E0031_RAW_PAIR_REPEATS: AtomicU64 = AtomicU64::new(0);
static E0031_SELECTED_SLOTS: AtomicU64 = AtomicU64::new(0);
static E0031_FRAME_HITS: AtomicU64 = AtomicU64::new(0);
static E0031_FRAME_MISSES: AtomicU64 = AtomicU64::new(0);
static E0031_HIT_SLOTS: AtomicU64 = AtomicU64::new(0);
static E0031_MISS_SLOTS: AtomicU64 = AtomicU64::new(0);
static E0031_CONS_ENTRIES: AtomicU64 = AtomicU64::new(0);
static E0031_FRAMED_ENTRIES: AtomicU64 = AtomicU64::new(0);
static E0031_SEEN_RAW: LazyLock<Mutex<HashSet<(usize, u64)>>> =
    LazyLock::new(|| Mutex::new(HashSet::new()));

pub fn print_e0031_stats() {
    eprintln!(
        "E0031_STATS cold_calls={} raw_pair_repeats={} selected_slots={} frame_hits={} frame_misses={} hit_slots={} miss_slots={} cons_entries={} framed_entries={}",
        E0031_COLD_CALLS.load(Relaxed),
        E0031_RAW_PAIR_REPEATS.load(Relaxed),
        E0031_SELECTED_SLOTS.load(Relaxed),
        E0031_FRAME_HITS.load(Relaxed),
        E0031_FRAME_MISSES.load(Relaxed),
        E0031_HIT_SLOTS.load(Relaxed),
        E0031_MISS_SLOTS.load(Relaxed),
        E0031_CONS_ENTRIES.load(Relaxed),
        E0031_FRAMED_ENTRIES.load(Relaxed),
    );
}
'''
assert marker in s
s = s.replace(marker, insert, 1)

old = """    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {
        let mut buf: [std::mem::MaybeUninit<V<'t>>; 64] = [const { std::mem::MaybeUninit::uninit() }; 64];
"""
new = """    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {
        E0031_COLD_CALLS.fetch_add(1, Relaxed);
        match e {
            value::Env::Cons { .. } => { E0031_CONS_ENTRIES.fetch_add(1, Relaxed); }
            value::Env::Framed { .. } => { E0031_FRAMED_ENTRIES.fetch_add(1, Relaxed); }
            value::Env::Nil { .. } => {}
        }
        {
            let pair = (e as *const value::Env<'t> as usize, mask);
            let mut seen = E0031_SEEN_RAW.lock().unwrap();
            if !seen.insert(pair) {
                E0031_RAW_PAIR_REPEATS.fetch_add(1, Relaxed);
            }
        }
        let mut buf: [std::mem::MaybeUninit<V<'t>>; 64] = [const { std::mem::MaybeUninit::uninit() }; 64];
"""
assert old in s
s = s.replace(old, new, 1)

old = """        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
"""
new = """        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        E0031_SELECTED_SLOTS.fetch_add(n as u64, Relaxed);
        let lsub = e.lsub();
        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let would_hit = self.tc_cache.frames.find(hash, |candidate: &E<'t>| match candidate {
            value::Env::Framed { mask: m, slots: sl, lsub: l, .. } =>
                *m == out_mask
                    && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                    && sl.len() == slots.len()
                    && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b)),
            _ => false,
        }).is_some();
        if would_hit {
            E0031_FRAME_HITS.fetch_add(1, Relaxed);
            E0031_HIT_SLOTS.fetch_add(n as u64, Relaxed);
        } else {
            E0031_FRAME_MISSES.fetch_add(1, Relaxed);
            E0031_MISS_SLOTS.fetch_add(n as u64, Relaxed);
        }
        let r = self.intern_frame(hash, out_mask, slots, lsub);
"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)

p = Path('a6/src/main.rs')
s = p.read_text()
old = """    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
new = """    if std::env::var_os(\"SOKONANODA_E0031_DIAG\").is_some() {
        sokonanoda::eval::print_e0031_stats();
    }
    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
