from pathlib import Path

p = Path('a6/src/eval.rs')
s = p.read_text()

start = s.index('    #[inline(never)]\n    fn prune_env_cold(&mut self, e: E<\'t>, mask: u64, slot: usize) -> E<\'t> {')
end = s.index('\n    #[inline]\n    pub(crate) fn key_env', start)
old = s[start:end]
new = '''    #[inline(never)]
    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {
        let mut buf: [std::mem::MaybeUninit<V<'t>>; 64] = [const { std::mem::MaybeUninit::uninit() }; 64];
        let mut slots_hash = e.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize as u64);
        let mut n = 0usize;
        let mut out_mask = 0u64;
        let mut rem = mask;
        while rem != 0 {
            let i = rem.trailing_zeros() as u16;
            rem &= rem - 1;
            if let Some(sv) = e.lookup(i) {
                buf[n].write(sv);
                slots_hash = slots_hash
                    .wrapping_mul(0x9E3779B97F4A7C15)
                    .wrapping_add(sv as *const Value<'t> as usize as u64);
                out_mask |= 1u64 << i;
                n += 1;
            }
        }
        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
        self.tc_cache.prune_dm[slot] = (e as *const value::Env<'t> as usize, mask, Some(r));
        match e {
            value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } => prune.set((mask, Some(r))),
            value::Env::Nil { .. } => {}
        }
        r
    }
'''
s = s[:start] + new + s[end:]
p.write_text(s)
