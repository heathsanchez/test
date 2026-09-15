from pathlib import Path

# Frozen adaptive spine representation.
# Threshold selected BEFORE hybrid performance by run 34926408611:
# max development-control peak + 1 = 64 + 1 = 65.
#
# Start every session with the exact A0 FxHashMap. On the 65th exact entry,
# migrate every interned spine to the exact prehashed HashTable and use only
# that representation for the remainder of the session.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const SESSION_MAP_CAP_SMALL: usize = 1 << 12;\n"
const_insert=const_marker+"pub(crate) const SPINE_RAW_THRESHOLD: usize = 65;\n"
assert const_marker in s
s=s.replace(const_marker,const_insert,1)

field_marker="    pub(crate) spine_hc: FxHashMap<(usize, u64), S<'a>>,\n"
field_insert=field_marker+"""    pub(crate) spine_hc_raw: HashTable<S<'a>>,
    pub(crate) spine_hc_raw_active: bool,
"""
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            spine_hc: session_fx_hash_map(),\n"
init_insert=init_marker+"""            spine_hc_raw: HashTable::new(),
            spine_hc_raw_active: false,
"""
assert init_marker in s
s=s.replace(init_marker,init_insert,1)

clear_marker="        self.spine_hc.clear();\n"
clear_insert=clear_marker+"""        self.spine_hc_raw.clear();
        self.spine_hc_raw_active = false;
"""
assert clear_marker in s
s=s.replace(clear_marker,clear_insert,1)

session_marker="        shrink_map(&mut self.spine_hc);\n"
session_insert=session_marker+"""        if self.spine_hc_raw.capacity() > KEEP_CAP {
            self.spine_hc_raw = HashTable::new();
        } else {
            self.spine_hc_raw.clear();
        }
        self.spine_hc_raw_active = false;
"""
assert session_marker in s
s=s.replace(session_marker,session_insert,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

marker="fn elim_key<'a>(elim: &Elim<'a>) -> u64 {\n    const _: () = assert!(std::mem::align_of::<Value<'static>>() >= 8);\n    elim.raw()\n}\n"
insert=marker+"""
#[inline]
fn spine_raw_hash(prev_addr: usize, elim_key: u64) -> u64 {
    (prev_addr as u64)
        .wrapping_mul(0x9E3779B97F4A7C15)
        .rotate_left(23)
        ^ elim_key.wrapping_mul(0xBF58476D1CE4E5B9)
}

#[inline]
fn stored_spine_raw_hash<'a>(s: S<'a>) -> u64 {
    match s {
        Spine::Snoc { prev, elim, .. } =>
            spine_raw_hash(*prev as *const Spine<'a> as usize, elim_key(elim)),
        Spine::Empty => 0,
    }
}

#[inline]
fn stored_spine_raw_matches<'a>(s: &S<'a>, prev_addr: usize, ekey: u64) -> bool {
    match s {
        Spine::Snoc { prev, elim, .. } =>
            *prev as *const Spine<'a> as usize == prev_addr && elim_key(elim) == ekey,
        Spine::Empty => false,
    }
}
"""
assert marker in s
s=s.replace(marker,insert,1)

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
        let prev_addr = prev as *const Spine<'t> as usize;
        let ekey = elim_key(&elim);

        if self.tc_cache.spine_hc_raw_active {
            let hash = spine_raw_hash(prev_addr, ekey);
            if let Some(s) = self.tc_cache.spine_hc_raw.find(
                hash,
                |s: &S<'t>| stored_spine_raw_matches(s, prev_addr, ekey),
            ) {
                return *s;
            }
            let s = value::spine_snoc(self.arena, prev, elim);
            let canon = prev.is_canonical()
                && match elim.view() {
                    ElimView::App(a) => a.is_canonical(),
                    ElimView::Proj { .. } => true,
                };
            if canon {
                s.mark_canonical();
            }
            self.tc_cache.spine_hc_raw.insert_unique(
                hash,
                s,
                |stored| stored_spine_raw_hash(*stored),
            );
            return s;
        }

        let key = (prev_addr, ekey);
        let arena = self.arena;
        let s = match self.tc_cache.spine_hc.entry(key) {
            Entry::Occupied(o) => return *o.get(),
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
        };

        if self.tc_cache.spine_hc.len() >= crate::util::SPINE_RAW_THRESHOLD {
            let mut raw = hashbrown::HashTable::with_capacity(self.tc_cache.spine_hc.len());
            for stored in self.tc_cache.spine_hc.values().copied() {
                let hash = stored_spine_raw_hash(stored);
                raw.insert_unique(hash, stored, |v| stored_spine_raw_hash(*v));
            }
            self.tc_cache.spine_hc_raw = raw;
            self.tc_cache.spine_hc.clear();
            self.tc_cache.spine_hc_raw_active = true;
        }
        s
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
