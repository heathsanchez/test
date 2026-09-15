from pathlib import Path

# Replace the authoritative spine interner with a prehashed HashTable<S>.
# Exact key law and canonical marking are unchanged.

p=Path("a6/src/util.rs")
s=p.read_text()

field_old="    pub(crate) spine_hc: FxHashMap<(usize, u64), S<'a>>,\n"
field_new="    pub(crate) spine_hc: HashTable<S<'a>>,\n"
assert field_old in s
s=s.replace(field_old,field_new,1)

init_old="            spine_hc: session_fx_hash_map(),\n"
init_new="            spine_hc: HashTable::with_capacity(SESSION_MAP_CAP),\n"
assert init_old in s
s=s.replace(init_old,init_new,1)

# clear() already uses .clear(), valid for HashTable.
session_old="        shrink_map(&mut self.spine_hc);\n"
session_new="""        if self.spine_hc.capacity() > KEEP_CAP {
            self.spine_hc = HashTable::with_capacity(SESSION_MAP_CAP);
        } else {
            self.spine_hc.clear();
        }
"""
assert session_old in s
s=s.replace(session_old,session_new,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

marker="fn elim_key<'a>(elim: &Elim<'a>) -> u64 {\n    const _: () = assert!(std::mem::align_of::<Value<'static>>() >= 8);\n    elim.raw()\n}\n"
insert=marker+"""
#[inline]
fn spine_hc_hash(prev_addr: usize, elim_key: u64) -> u64 {
    (prev_addr as u64)
        .wrapping_mul(0x9E3779B97F4A7C15)
        .rotate_left(23)
        ^ elim_key.wrapping_mul(0xBF58476D1CE4E5B9)
}

#[inline]
fn stored_spine_hc_hash<'a>(s: S<'a>) -> u64 {
    match s {
        Spine::Snoc { prev, elim, .. } =>
            spine_hc_hash(prev as *const Spine<'a> as usize, elim_key(elim)),
        Spine::Empty => 0,
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
        let hash = spine_hc_hash(prev_addr, ekey);

        if let Some(s) = self.tc_cache.spine_hc.find(hash, |s: &S<'t>| match s {
            Spine::Snoc { prev: p, elim: e, .. } =>
                *p as *const Spine<'t> as usize == prev_addr && elim_key(e) == ekey,
            Spine::Empty => false,
        }) {
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
        self.tc_cache.spine_hc.insert_unique(hash, s, |stored| stored_spine_hc_hash(*stored));
        s
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
