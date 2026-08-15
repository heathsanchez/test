from pathlib import Path

SESSION_BUDGET = 2_621_440

for root in ('a2','e0015'):
    p=Path(root)/'src/tc.rs'; s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))

p=Path('e0015/src/eval.rs'); s=p.read_text()
anchor='''    #[inline(never)]\n    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {\n'''
assert anchor in s
insert='''    #[inline]\n    fn prune_singleton(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {\n        debug_assert!(mask != 0 && mask.count_ones() == 1);\n        let idx = mask.trailing_zeros() as u16;\n        let Some(v) = e.lookup(idx) else {\n            return self.lsub_base(e.lsub());\n        };\n        let lsub = e.lsub();\n        let mut slots_hash = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize as u64);\n        slots_hash = slots_hash\n            .wrapping_mul(0x9E3779B97F4A7C15)\n            .wrapping_add(v as *const Value<'t> as usize as u64);\n        let one = [v];\n        let hash = mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);\n        let r = self.intern_frame(hash, mask, &one, lsub);\n        self.tc_cache.prune_dm[slot] = (e as *const value::Env<'t> as usize, mask, Some(r));\n        match e {\n            value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } => prune.set((mask, Some(r))),\n            value::Env::Nil { .. } => {}\n        }\n        r\n    }\n\n'''
s=s.replace(anchor,insert+anchor,1)
old='''        self.prune_env_cold(e, mask, slot)\n    }\n'''
new='''        if mask.count_ones() == 1 {\n            return self.prune_singleton(e, mask, slot);\n        }\n        self.prune_env_cold(e, mask, slot)\n    }\n'''
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
