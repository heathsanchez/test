from pathlib import Path

# Reconstruct both arms from upstream, then apply A3 (E0018) to both.
SESSION_BUDGET = 2_621_440
for root in ('a3','e0019'):
    p = Path(root) / 'src/tc.rs'
    s = p.read_text()
    old = 'const SESSION_BUDGET: usize = 1 << 20;'
    assert old in s
    p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

    p = Path(root) / 'src/eval.rs'
    s = p.read_text()
    old = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                let pruned = self.key_env(env, body);
                env = value::env_extend(self.arena, pruned, args[i]);
                body = inner;
                i += 1;
"""
    new = """                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                env = value::env_extend(self.arena, env, args[i]);
                body = inner;
                i += 1;
"""
    assert old in s, f'A3 apply_many block not found in {root}'
    p.write_text(s.replace(old, new, 1))

# E0019 only: add an exact-checked direct-mapped L0 in front of the frame HashTable.
p = Path('e0019/src/util.rs')
s = p.read_text()
old = "pub(crate) const PRUNE_DM_LEN: usize = 1 << 10;\npub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
new = "pub(crate) const PRUNE_DM_LEN: usize = 1 << 10;\npub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\npub(crate) const FRAME_DM_LEN: usize = 1 << 12;\npub(crate) const FRAME_DM_SHIFT: u32 = 64 - 12;\n"
assert old in s
s = s.replace(old,new,1)
old = """    pub(crate) frames: hashbrown::HashTable<E<'a>>,
    pub(crate) lsub_bases: FxHashMap<usize, E<'a>>,
"""
new = """    pub(crate) frames: hashbrown::HashTable<E<'a>>,
    pub(crate) frame_dm: Box<[(u64, Option<E<'a>>); FRAME_DM_LEN]>,
    pub(crate) lsub_bases: FxHashMap<usize, E<'a>>,
"""
assert old in s
s=s.replace(old,new,1)
old = """            frames: hashbrown::HashTable::with_capacity(SESSION_MAP_CAP),
            lsub_bases: small_fx_hash_map(),
"""
new = """            frames: hashbrown::HashTable::with_capacity(SESSION_MAP_CAP),
            frame_dm: Box::new([(0, None); FRAME_DM_LEN]),
            lsub_bases: small_fx_hash_map(),
"""
assert old in s
s=s.replace(old,new,1)
old = """        self.frames.clear();
        self.lsub_bases.clear();
"""
new = """        self.frames.clear();
        self.frame_dm.fill((0, None));
        self.lsub_bases.clear();
"""
assert old in s
s=s.replace(old,new,1)
old = """        if self.frames.capacity() > KEEP_CAP {
            self.frames = hashbrown::HashTable::new();
        } else {
            self.frames.clear();
        }
        shrink_map(&mut self.lsub_bases);
"""
new = """        if self.frames.capacity() > KEEP_CAP {
            self.frames = hashbrown::HashTable::new();
        } else {
            self.frames.clear();
        }
        self.frame_dm.fill((0, None));
        shrink_map(&mut self.lsub_bases);
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p = Path('e0019/src/eval.rs')
s = p.read_text()
old = """        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
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
"""
new = """        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let dm_slot = (hash >> crate::util::FRAME_DM_SHIFT) as usize;
        let dm = self.tc_cache.frame_dm[dm_slot];
        if dm.0 == hash {
            if let Some(e) = dm.1 {
                if let value::Env::Framed { mask: m, slots: sl, lsub: l, .. } = e {
                    if *m == mask
                        && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                        && sl.len() == slots.len()
                        && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b))
                    {
                        return e;
                    }
                }
            }
        }
        if let Some(e) = self.tc_cache.frames.find(hash, |e: &E<'t>| match e {
            value::Env::Framed { mask: m, slots: sl, lsub: l, .. } =>
                *m == mask
                    && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                    && sl.len() == slots.len()
                    && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b)),
            _ => false,
        }) {
            self.tc_cache.frame_dm[dm_slot] = (hash, Some(e));
            return e;
        }
"""
assert old in s, 'intern_frame lookup block not found'
s=s.replace(old,new,1)
old = """        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        e
"""
new = """        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        self.tc_cache.frame_dm[dm_slot] = (hash, Some(e));
        e
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
