from pathlib import Path

# RED diagnostic for an opportunistic canonical-slot quotient.
#
# Unlike the broad rejected candidate, this does NOT call
# canonicalize_for_spine() on projected slots. It only asks whether the checker
# has ALREADY earned a canonical representative through normal execution:
#
#   - v.is_canonical() => v is already canonical
#   - tc_cache.canon_cache[raw_ptr] => an existing normal-path canonicalization
#   - otherwise keep v raw
#
# The actual projected frame remains unchanged. If distinct raw frame vectors
# collapse under these already-earned representatives, then a quotient is
# available without paying canonicalization acquisition cost on this path.

p = Path("a6/src/util.rs")
s = p.read_text()

field_marker = "    pub(crate) frames: hashbrown::HashTable<E<'a>>,\n"
field_insert = field_marker + (
    "    pub(crate) cq_earned_seen: "
    "FxHashMap<(u64, usize, Vec<usize>), Vec<usize>>,\n"
)
assert field_marker in s
s = s.replace(field_marker, field_insert, 1)

init_marker = "            frames: hashbrown::HashTable::with_capacity(SESSION_MAP_CAP),\n"
init_insert = init_marker + "            cq_earned_seen: FxHashMap::default(),\n"
assert init_marker in s
s = s.replace(init_marker, init_insert, 1)

clear_marker = "        self.frames.clear();\n"
clear_insert = clear_marker + "        self.cq_earned_seen.clear();\n"
assert clear_marker in s
s = s.replace(clear_marker, clear_insert, 1)

session_marker = """        if self.frames.capacity() > KEEP_CAP {
            self.frames = hashbrown::HashTable::new();
        } else {
            self.frames.clear();
        }
"""
session_insert = session_marker + "        shrink_map(&mut self.cq_earned_seen);\n"
assert session_marker in s
s = s.replace(session_marker, session_insert, 1)

p.write_text(s)

p = Path("a6/src/eval.rs")
s = p.read_text()

s = s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + """
static CQ_EARNED_CALLS: AtomicU64 = AtomicU64::new(0);
static CQ_EARNED_SLOT_TOTAL: AtomicU64 = AtomicU64::new(0);
static CQ_EARNED_SLOT_HITS: AtomicU64 = AtomicU64::new(0);
static CQ_EARNED_FRAME_CHANGED: AtomicU64 = AtomicU64::new(0);
static CQ_EARNED_CANON_REPEAT: AtomicU64 = AtomicU64::new(0);
static CQ_EARNED_FALSE_SPLITS: AtomicU64 = AtomicU64::new(0);

pub fn print_cq_earned_red_stats() {
    eprintln!(
        "CQ_EARNED_RED calls={} slot_total={} slot_hits={} frame_changed={} canon_repeat={} false_splits={}",
        CQ_EARNED_CALLS.load(Relaxed),
        CQ_EARNED_SLOT_TOTAL.load(Relaxed),
        CQ_EARNED_SLOT_HITS.load(Relaxed),
        CQ_EARNED_FRAME_CHANGED.load(Relaxed),
        CQ_EARNED_CANON_REPEAT.load(Relaxed),
        CQ_EARNED_FALSE_SPLITS.load(Relaxed),
    );
}
"""
assert marker in s
s = s.replace(marker, insert, 1)

old = """        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
"""
new = """        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();

        // RED diagnostic only. Read already-earned canonical representatives
        // without invoking canonicalization and without changing the real frame.
        CQ_EARNED_CALLS.fetch_add(1, Relaxed);
        CQ_EARNED_SLOT_TOTAL.fetch_add(slots.len() as u64, Relaxed);
        let raw_ptrs: Vec<usize> =
            slots.iter().map(|v| *v as *const Value<'t> as usize).collect();
        let earned_values: Vec<V<'t>> = slots.iter().copied().map(|v| {
            if v.is_canonical() {
                v
            } else {
                let key = v as *const Value<'t> as usize;
                self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
            }
        }).collect();
        let earned_ptrs: Vec<usize> =
            earned_values.iter().map(|v| *v as *const Value<'t> as usize).collect();
        let hit_count = raw_ptrs.iter().zip(&earned_ptrs).filter(|(a,b)| a != b).count();
        if hit_count != 0 {
            CQ_EARNED_SLOT_HITS.fetch_add(hit_count as u64, Relaxed);
            CQ_EARNED_FRAME_CHANGED.fetch_add(1, Relaxed);
        }

        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let diag_key = (out_mask, lsub_addr, earned_ptrs);
        match self.tc_cache.cq_earned_seen.entry(diag_key) {
            std::collections::hash_map::Entry::Occupied(o) => {
                CQ_EARNED_CANON_REPEAT.fetch_add(1, Relaxed);
                if o.get() != &raw_ptrs {
                    CQ_EARNED_FALSE_SPLITS.fetch_add(1, Relaxed);
                }
            }
            std::collections::hash_map::Entry::Vacant(v) => {
                v.insert(raw_ptrs);
            }
        }

        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)

p = Path("a6/src/main.rs")
s = p.read_text()
old = """    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new = """    if std::env::var_os("SOKONANODA_CQ_EARNED_RED").is_some() {
        sokonanoda::eval::print_cq_earned_red_stats();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
