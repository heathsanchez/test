from pathlib import Path

p = Path('a6/src/eval.rs')
s = p.read_text()
old = '''    fn intern_frame(
        &mut self,
        hash: u64,
        mask: u64,
        slots: &[V<'t>],
        lsub: Option<&'t value::LevelSub<'t>>,
    ) -> E<'t> {
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        if let Some(e) = self.tc_cache.frames.find(hash, |e: &E<'t>| match e {
            value::Env::Framed { mask: m, slots: sl, lsub: l, .. } =>
                *m == mask
                    && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                    && sl.len() == slots.len()
                    && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b)),
            _ => false,
        }) {
            return e;
        }
        let len = 64 - mask.leading_zeros();
        let e: E<'t> = self.arena.alloc(value::Env::Framed {
            mask,
            slots: self.arena.alloc_slice_copy(slots),
            lsub,
            hash,
            len,
            prune: std::cell::Cell::new((0, None)),
        });
        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        e
    }
'''
new = '''    fn intern_frame(
        &mut self,
        hash: u64,
        mask: u64,
        slots: &[V<'t>],
        lsub: Option<&'t value::LevelSub<'t>>,
    ) -> E<'t> {
        // E0035 causal ablation: preserve projection semantics and frame contents,
        // but remove quotient identity reuse by always allocating a fresh frame.
        let len = 64 - mask.leading_zeros();
        self.arena.alloc(value::Env::Framed {
            mask,
            slots: self.arena.alloc_slice_copy(slots),
            lsub,
            hash,
            len,
            prune: std::cell::Cell::new((0, None)),
        })
    }
'''
assert old in s
p.write_text(s.replace(old, new, 1))
