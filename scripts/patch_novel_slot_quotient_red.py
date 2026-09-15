from pathlib import Path

# RED diagnostic for a novel consequence quotient:
#
# Current frame interning keys projected slots by raw Value pointer identity.
# This instrumentation asks whether two different raw slot-pointer vectors
# collapse to the same vector after the checker's existing
# canonicalize_for_spine() operation.
#
# If yes, current A6 contains a representational false split:
# distinct frame identities that existing value canonicalization already says
# are interchangeable.
#
# This patch is diagnostic only. It does NOT alter the slots stored in frames
# and does NOT enable the candidate quotient.

p = Path("a6/src/util.rs")
s = p.read_text()

field_marker = "    pub(crate) frames: hashbrown::HashTable<E<'a>>,\n"
field_insert = field_marker + (
    "    pub(crate) cq_slot_seen: "
    "FxHashMap<(u64, usize, Vec<usize>), Vec<usize>>,\n"
)
assert field_marker in s
s = s.replace(field_marker, field_insert, 1)

init_marker = "            frames: hashbrown::HashTable::with_capacity(SESSION_MAP_CAP),\n"
init_insert = init_marker + "            cq_slot_seen: FxHashMap::default(),\n"
assert init_marker in s
s = s.replace(init_marker, init_insert, 1)

clear_marker = "        self.frames.clear();\n"
clear_insert = clear_marker + "        self.cq_slot_seen.clear();\n"
assert clear_marker in s
s = s.replace(clear_marker, clear_insert, 1)

session_marker = """        if self.frames.capacity() > KEEP_CAP {
            self.frames = hashbrown::HashTable::new();
        } else {
            self.frames.clear();
        }
"""
session_insert = session_marker + "        shrink_map(&mut self.cq_slot_seen);\n"
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
static CQ_SLOT_CALLS: AtomicU64 = AtomicU64::new(0);
static CQ_SLOT_CANON_CHANGED: AtomicU64 = AtomicU64::new(0);
static CQ_SLOT_CANON_REPEAT: AtomicU64 = AtomicU64::new(0);
static CQ_SLOT_FALSE_SPLITS: AtomicU64 = AtomicU64::new(0);

pub fn print_cq_slot_red_stats() {
    eprintln!(
        "CQ_SLOT_RED calls={} canon_changed={} canon_repeat={} false_splits={}",
        CQ_SLOT_CALLS.load(Relaxed),
        CQ_SLOT_CANON_CHANGED.load(Relaxed),
        CQ_SLOT_CANON_REPEAT.load(Relaxed),
        CQ_SLOT_FALSE_SPLITS.load(Relaxed),
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

        // RED diagnostic only: derive the representation that would result if
        // projected slot values were first passed through the checker's existing
        // canonicalization. Do not use these canonical slots for the actual frame.
        CQ_SLOT_CALLS.fetch_add(1, Relaxed);
        let raw_ptrs: Vec<usize> =
            slots.iter().map(|v| *v as *const Value<'t> as usize).collect();
        let canonical_values: Vec<V<'t>> =
            slots.iter().copied().map(|v| self.canonicalize_for_spine(v)).collect();
        let canonical_ptrs: Vec<usize> =
            canonical_values.iter().map(|v| *v as *const Value<'t> as usize).collect();
        if raw_ptrs != canonical_ptrs {
            CQ_SLOT_CANON_CHANGED.fetch_add(1, Relaxed);
        }
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let diag_key = (out_mask, lsub_addr, canonical_ptrs);
        match self.tc_cache.cq_slot_seen.entry(diag_key) {
            std::collections::hash_map::Entry::Occupied(o) => {
                CQ_SLOT_CANON_REPEAT.fetch_add(1, Relaxed);
                if o.get() != &raw_ptrs {
                    CQ_SLOT_FALSE_SPLITS.fetch_add(1, Relaxed);
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
new = """    if std::env::var_os("SOKONANODA_CQ_SLOT_RED").is_some() {
        sokonanoda::eval::print_cq_slot_red_stats();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
