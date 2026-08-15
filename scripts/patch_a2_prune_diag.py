from pathlib import Path

SESSION_BUDGET = 2_621_440

p = Path('a2/src/tc.rs')
s = p.read_text()
old = 'const SESSION_BUDGET: usize = 1 << 20;'
assert old in s
p.write_text(s.replace(old, f'const SESSION_BUDGET: usize = {SESSION_BUDGET};', 1))

p = Path('a2/src/eval.rs')
s = p.read_text()
anchor = 'use std::collections::hash_map::Entry;\n'
insert = '''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static PRUNE_TOTAL: AtomicU64 = AtomicU64::new(0);
static PRUNE_MASK0: AtomicU64 = AtomicU64::new(0);
static PRUNE_SUBSET: AtomicU64 = AtomicU64::new(0);
static PRUNE_CELL_HIT: AtomicU64 = AtomicU64::new(0);
static PRUNE_CELL_MISMATCH: AtomicU64 = AtomicU64::new(0);
static PRUNE_DM_HIT: AtomicU64 = AtomicU64::new(0);
static PRUNE_DM_OCCUPIED_MISS: AtomicU64 = AtomicU64::new(0);
static PRUNE_COLD: AtomicU64 = AtomicU64::new(0);
static PRUNE_COLD_CONS: AtomicU64 = AtomicU64::new(0);
static PRUNE_COLD_FRAMED: AtomicU64 = AtomicU64::new(0);

pub fn dump_prune_stats() {
    eprintln!("PRUNE_STATS total={} mask0={} subset={} cell_hit={} cell_mismatch={} dm_hit={} dm_occupied_miss={} cold={} cold_cons={} cold_framed={}",
        PRUNE_TOTAL.load(Relaxed), PRUNE_MASK0.load(Relaxed), PRUNE_SUBSET.load(Relaxed),
        PRUNE_CELL_HIT.load(Relaxed), PRUNE_CELL_MISMATCH.load(Relaxed),
        PRUNE_DM_HIT.load(Relaxed), PRUNE_DM_OCCUPIED_MISS.load(Relaxed), PRUNE_COLD.load(Relaxed),
        PRUNE_COLD_CONS.load(Relaxed), PRUNE_COLD_FRAMED.load(Relaxed));
}
'''
assert anchor in s
s = s.replace(anchor, anchor + insert, 1)

old = '''    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {
        if mask == 0 {
            return self.lsub_base(e.lsub());
        }'''
new = '''    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {
        PRUNE_TOTAL.fetch_add(1, Relaxed);
        if mask == 0 {
            PRUNE_MASK0.fetch_add(1, Relaxed);
            return self.lsub_base(e.lsub());
        }'''
assert old in s
s = s.replace(old, new, 1)

old = '''                if *m & mask == *m {
                    return e
                }'''
new = '''                if *m & mask == *m {
                    PRUNE_SUBSET.fetch_add(1, Relaxed);
                    return e
                }'''
assert old in s
s = s.replace(old, new, 1)

old = '''                if m == mask {
                    if let Some(r) = r {
                        return r;
                    }
                }'''
new = '''                if m == mask {
                    if let Some(r) = r {
                        PRUNE_CELL_HIT.fetch_add(1, Relaxed);
                        return r;
                    }
                } else if r.is_some() {
                    PRUNE_CELL_MISMATCH.fetch_add(1, Relaxed);
                }'''
assert s.count(old) == 2
s = s.replace(old, new, 2)

old = '''        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        self.prune_env_cold(e, mask, slot)'''
new = '''        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                PRUNE_DM_HIT.fetch_add(1, Relaxed);
                return hit;
            }
        } else if ent.2.is_some() {
            PRUNE_DM_OCCUPIED_MISS.fetch_add(1, Relaxed);
        }
        PRUNE_COLD.fetch_add(1, Relaxed);
        match e {
            value::Env::Cons { .. } => { PRUNE_COLD_CONS.fetch_add(1, Relaxed); }
            value::Env::Framed { .. } => { PRUNE_COLD_FRAMED.fetch_add(1, Relaxed); }
            value::Env::Nil { .. } => {}
        }
        self.prune_env_cold(e, mask, slot)'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)

p = Path('a2/src/main.rs')
s = p.read_text()
old = '''    export_file.check_all_declars();
    // Pretty print as necessary'''
new = '''    export_file.check_all_declars();
    sokonanoda::eval::dump_prune_stats();
    // Pretty print as necessary'''
assert old in s
p.write_text(s.replace(old, new, 1))
