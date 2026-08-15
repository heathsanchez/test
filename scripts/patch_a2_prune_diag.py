from pathlib import Path

SESSION_BUDGET=2_621_440

p=Path('a2/src/tc.rs'); s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'
assert old in s
p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))

p=Path('a2/src/eval.rs'); s=p.read_text()
anchor='use std::collections::hash_map::Entry;\n'
insert='''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n\nstatic PRUNE_TOTAL: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_MASK0: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_SUBSET: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_CELL_HIT: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_CELL_MISMATCH: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_DM_HIT: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_DM_MISMATCH: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_COLD: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_COLD_CONS: AtomicU64 = AtomicU64::new(0);\nstatic PRUNE_COLD_FRAMED: AtomicU64 = AtomicU64::new(0);\n\npub fn dump_prune_stats() {\n    eprintln!(\"PRUNE_STATS total={} mask0={} subset={} cell_hit={} cell_mismatch={} dm_hit={} dm_mismatch={} cold={} cold_cons={} cold_framed={}\",\n        PRUNE_TOTAL.load(Relaxed), PRUNE_MASK0.load(Relaxed), PRUNE_SUBSET.load(Relaxed),\n        PRUNE_CELL_HIT.load(Relaxed), PRUNE_CELL_MISMATCH.load(Relaxed),\n        PRUNE_DM_HIT.load(Relaxed), PRUNE_DM_MISMATCH.load(Relaxed), PRUNE_COLD.load(Relaxed),\n        PRUNE_COLD_CONS.load(Relaxed), PRUNE_COLD_FRAMED.load(Relaxed));\n}\n'''
assert anchor in s
s=s.replace(anchor,anchor+insert,1)

old='''    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {\n        if mask == 0 {\n            return self.lsub_base(e.lsub());\n        }'''
new='''    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {\n        PRUNE_TOTAL.fetch_add(1, Relaxed);\n        if mask == 0 {\n            PRUNE_MASK0.fetch_add(1, Relaxed);\n            return self.lsub_base(e.lsub());\n        }'''
assert old in s; s=s.replace(old,new,1)

old='''                if *m & mask == *m {\n                    return e\n                }'''
new='''                if *m & mask == *m {\n                    PRUNE_SUBSET.fetch_add(1, Relaxed);\n                    return e\n                }'''
assert old in s; s=s.replace(old,new,1)

old='''                if m == mask {\n                    if let Some(r) = r {\n                        return r;\n                    }\n                }'''
new='''                if m == mask {\n                    if let Some(r) = r {\n                        PRUNE_CELL_HIT.fetch_add(1, Relaxed);\n                        return r;\n                    }\n                } else if r.is_some() {\n                    PRUNE_CELL_MISMATCH.fetch_add(1, Relaxed);\n                }'''
assert s.count(old)==2
s=s.replace(old,new,2)

old='''        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {\n            if let Some(hit) = ent.2 {\n                match e {'''
new='''        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {\n            if let Some(hit) = ent.2 {\n                match e {'''
assert old in s
# leave opening block unchanged; insert mismatch before cold
old='''                PRUNE_DM_HIT.fetch_add(1, Relaxed);\n                return hit;\n            }\n        }\n        PRUNE_COLD.fetch_add(1, Relaxed);'''
new='''                PRUNE_DM_HIT.fetch_add(1, Relaxed);\n                return hit;\n            }\n        } else if ent.2.is_some() {\n            PRUNE_DM_MISMATCH.fetch_add(1, Relaxed);\n        }\n        PRUNE_COLD.fetch_add(1, Relaxed);'''
# PRUNE_DM_HIT isn't in upstream yet, add it first via the upstream block
up='''                return hit;\n            }\n        }\n        PRUNE_COLD.fetch_add(1, Relaxed);'''
if up in s:
    s=s.replace(up,'''                PRUNE_DM_HIT.fetch_add(1, Relaxed);\n                return hit;\n            }\n        } else if ent.2.is_some() {\n            PRUNE_DM_MISMATCH.fetch_add(1, Relaxed);\n        }\n        PRUNE_COLD.fetch_add(1, Relaxed);''',1)
else:
    raise RuntimeError('direct-map block not found')

old='''        match e {\n            value::Env::Cons { .. } => { PRUNE_COLD_CONS.fetch_add(1, Relaxed); }\n            value::Env::Framed { .. } => { PRUNE_COLD_FRAMED.fetch_add(1, Relaxed); }\n            value::Env::Nil { .. } => {}\n        }\n        self.prune_env_cold(e, mask, slot)'''
# Upstream doesn't have this yet; append before cold call.
if old not in s:
    target='''        self.prune_env_cold(e, mask, slot)'''
    repl='''        match e {\n            value::Env::Cons { .. } => { PRUNE_COLD_CONS.fetch_add(1, Relaxed); }\n            value::Env::Framed { .. } => { PRUNE_COLD_FRAMED.fetch_add(1, Relaxed); }\n            value::Env::Nil { .. } => {}\n        }\n        self.prune_env_cold(e, mask, slot)'''
    assert target in s; s=s.replace(target,repl,1)
p.write_text(s)

p=Path('a2/src/main.rs'); s=p.read_text()
old='''    export_file.check_all_declars();\n    // Pretty print as necessary'''
new='''    export_file.check_all_declars();\n    sokonanoda::eval::dump_prune_stats();\n    // Pretty print as necessary'''
assert old in s; p.write_text(s.replace(old,new,1))
