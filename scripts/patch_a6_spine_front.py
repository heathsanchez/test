from pathlib import Path

# Production experiment: exact 4K front cache before spine_hc only.
# Locality run 34923791015 predicted 90.59% capture of current spine_hc hits
# across the frozen four-case development workload.
#
# Safety: full current key is stored and compared before returning. Misses fall
# through unchanged to the authoritative spine_hc map.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
insert=const_marker+"pub(crate) const SPINE_FRONT_LEN: usize = 1 << 12;\n"
assert const_marker in s
s=s.replace(const_marker,insert,1)

field_marker="    pub(crate) spine_hc: FxHashMap<(usize, u64), S<'a>>,\n"
field=field_marker+"    pub(crate) spine_front: Box<[Option<(usize, u64, S<'a>)>; SPINE_FRONT_LEN]>,\n"
assert field_marker in s
s=s.replace(field_marker,field,1)

init_marker="            spine_hc: session_fx_hash_map(),\n"
init=init_marker+"            spine_front: Box::new([None; SPINE_FRONT_LEN]),\n"
assert init_marker in s
s=s.replace(init_marker,init,1)

clear_marker="        self.spine_hc.clear();\n"
clear=clear_marker+"        self.spine_front.fill(None);\n"
assert clear_marker in s
s=s.replace(clear_marker,clear,1)

session_marker="        shrink_map(&mut self.spine_hc);\n"
session=session_marker+"        self.spine_front.fill(None);\n"
assert session_marker in s
s=s.replace(session_marker,session,1)

p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
helper=marker+"""
#[inline]
fn spine_front_index(key: (usize, u64)) -> usize {
    let h = (key.0 as u64)
        .wrapping_mul(0x9E3779B97F4A7C15)
        .rotate_left(23)
        ^ key.1.wrapping_mul(0xBF58476D1CE4E5B9);
    h as usize & (crate::util::SPINE_FRONT_LEN - 1)
}
"""
assert marker in s
s=s.replace(marker,helper,1)

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
        let front_i = spine_front_index(key);
        if let Some((kp, ke, s)) = self.tc_cache.spine_front[front_i] {
            if kp == key.0 && ke == key.1 {
                return s;
            }
        }

        let arena = self.arena;
        let s = match self.tc_cache.spine_hc.entry(key) {
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
        };
        self.tc_cache.spine_front[front_i] = Some((key.0, key.1, s));
        s
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
