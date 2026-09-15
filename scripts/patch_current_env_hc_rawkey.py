from pathlib import Path

# Current official sokonanoda: replace only env_hc with an exact prehashed
# HashTable<(parent_ptr, value_ptr, Env)>. Identity is materialized alongside
# the authoritative environment.

p=Path("a6/src/util.rs")
s=p.read_text()

old="    pub(crate) env_hc: FxHashMap<(usize, usize), E<'a>>,\n"
new="    pub(crate) env_hc: HashTable<(usize, usize, E<'a>)>,\n"
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
    fn env_hc_hash(key: (usize, usize)) -> u64 {
        crate::hash64!(key.0, key.1)
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
        let key = (
            parent as *const value::Env<'t> as usize,
            v as *const Value<'t> as usize,
        );
        let hash = Self::env_hc_hash(key);
        if let Some(entry) = self.tc_cache.env_hc.find(
            hash,
            |entry| entry.0 == key.0 && entry.1 == key.1,
        ) {
            return entry.2;
        }
        let e = value::env_extend(self.arena, parent, v);
        self.tc_cache.env_hc.insert_unique(
            hash,
            (key.0, key.1, e),
            |entry| Self::env_hc_hash((entry.0, entry.1)),
        );
        e
    }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
