from pathlib import Path
import argparse

ap=argparse.ArgumentParser()
ap.add_argument("--k",type=int,required=True,choices=[1,2,4,8,16])
args=ap.parse_args()
K=args.k

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
insert=const_marker+f"pub(crate) const SPINE_RECENT_LEN: usize = {K};\n"
assert const_marker in s
s=s.replace(const_marker,insert,1)

field_marker="    pub(crate) spine_hc: FxHashMap<(usize, u64), S<'a>>,\n"
field=field_marker+"""    pub(crate) spine_recent: [Option<(usize, u64, S<'a>)>; SPINE_RECENT_LEN],
    pub(crate) spine_recent_pos: usize,
"""
assert field_marker in s
s=s.replace(field_marker,field,1)

init_marker="            spine_hc: session_fx_hash_map(),\n"
init=init_marker+"""            spine_recent: [None; SPINE_RECENT_LEN],
            spine_recent_pos: 0,
"""
assert init_marker in s
s=s.replace(init_marker,init,1)

clear_marker="        self.spine_hc.clear();\n"
clear=clear_marker+"""        self.spine_recent.fill(None);
        self.spine_recent_pos = 0;
"""
assert clear_marker in s
s=s.replace(clear_marker,clear,1)

session_marker="        shrink_map(&mut self.spine_hc);\n"
session=session_marker+"""        self.spine_recent.fill(None);
        self.spine_recent_pos = 0;
"""
assert session_marker in s
s=s.replace(session_marker,session,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

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

        let mut recent_hit = None;
        for ent in self.tc_cache.spine_recent.iter() {
            if let Some((kp, ke, s)) = *ent {
                if kp == key.0 && ke == key.1 {
                    recent_hit = Some(s);
                    break;
                }
            }
        }
        if let Some(s) = recent_hit {
            let pos = self.tc_cache.spine_recent_pos;
            self.tc_cache.spine_recent[pos] = Some((key.0, key.1, s));
            self.tc_cache.spine_recent_pos = (pos + 1) & (crate::util::SPINE_RECENT_LEN - 1);
            return s;
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
        let pos = self.tc_cache.spine_recent_pos;
        self.tc_cache.spine_recent[pos] = Some((key.0, key.1, s));
        self.tc_cache.spine_recent_pos = (pos + 1) & (crate::util::SPINE_RECENT_LEN - 1);
        s
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
