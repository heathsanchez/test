from pathlib import Path

# Current official sokonanoda: replace only env_hc with an exact prehashed
# HashTable<E>. Exact key is still (parent pointer, value pointer), reconstructed
# from the stored Env::Cons for equality/rehash.

p=Path("a6/src/util.rs")
s=p.read_text()

old="    pub(crate) env_hc: FxHashMap<(usize, usize), E<'a>>,\n"
new="    pub(crate) env_hc: HashTable<E<'a>>,\n"
assert old in s
s=s.replace(old,new,1)

old="            env_hc: session_fx_hash_map(),\n"
new="            env_hc: HashTable::with_capacity(SESSION_MAP_CAP),\n"
assert old in s
s=s.replace(old,new,1)

old="        shrink_map(&mut self.env_hc);\n"
new="""        if self.env_hc.capacity() > KEEP_CAP {
            self.env_hc = HashTable::new();
        } else {
            self.env_hc.clear();
        }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

marker="""    pub(crate) fn env_extend(&mut self, parent: E<'t>, v: V<'t>) -> E<'t> {
"""
helper="""    #[inline]
    fn env_hc_key(parent: E<'t>, v: V<'t>) -> (usize, usize) {
        (
            parent as *const value::Env<'t> as usize,
            v as *const Value<'t> as usize,
        )
    }

    #[inline]
    fn env_hc_hash(key: (usize, usize)) -> u64 {
        crate::hash64!(key.0, key.1)
    }

    #[inline]
    fn stored_env_hc_key(e: E<'t>) -> (usize, usize) {
        match e {
            value::Env::Cons { v, parent, .. } => (
                *parent as *const value::Env<'t> as usize,
                *v as *const Value<'t> as usize,
            ),
            _ => unreachable!("env_hc stores only Env::Cons"),
        }
    }

"""+marker
assert marker in s
s=s.replace(marker,helper,1)

old="""    pub(crate) fn env_extend(&mut self, parent: E<'t>, v: V<'t>) -> E<'t> {
        let key = (parent as *const value::Env<'t> as usize, v as *const Value<'t> as usize);
        match self.tc_cache.env_hc.entry(key) {
            Entry::Occupied(o) => o.get(),
            Entry::Vacant(slot) => slot.insert(value::env_extend(self.arena, parent, v)),
        }
    }
"""
new="""    pub(crate) fn env_extend(&mut self, parent: E<'t>, v: V<'t>) -> E<'t> {
        let key = Self::env_hc_key(parent, v);
        let hash = Self::env_hc_hash(key);
        if let Some(e) = self.tc_cache.env_hc.find(hash, |stored| Self::stored_env_hc_key(*stored) == key) {
            return *e;
        }
        let e = value::env_extend(self.arena, parent, v);
        self.tc_cache.env_hc.insert_unique(
            hash,
            e,
            |stored| Self::env_hc_hash(Self::stored_env_hc_key(*stored)),
        );
        e
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
