from pathlib import Path

SESSION_BUDGET = 2_621_440

p=Path('a2/src/tc.rs'); s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'; assert old in s
p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))

p=Path('a2/src/eval.rs'); s=p.read_text()
anchor='use std::collections::hash_map::Entry;\n'
insert='''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static COLD_TOTAL: AtomicU64 = AtomicU64::new(0);
static COLD_PC1: AtomicU64 = AtomicU64::new(0);
static COLD_PC2: AtomicU64 = AtomicU64::new(0);
static COLD_PC3: AtomicU64 = AtomicU64::new(0);
static COLD_PC4P: AtomicU64 = AtomicU64::new(0);
static COLD_POPSUM: AtomicU64 = AtomicU64::new(0);
static COLD_SPANSUM: AtomicU64 = AtomicU64::new(0);
static COLD_SPAN8: AtomicU64 = AtomicU64::new(0);
static COLD_SPAN16: AtomicU64 = AtomicU64::new(0);
static COLD_SPAN32: AtomicU64 = AtomicU64::new(0);
static COLD_SPAN64: AtomicU64 = AtomicU64::new(0);
static COLD_CONS: AtomicU64 = AtomicU64::new(0);
static COLD_FRAMED: AtomicU64 = AtomicU64::new(0);

pub fn dump_prune_shape_stats() {
    eprintln!("PRUNE_SHAPE cold={} pc1={} pc2={} pc3={} pc4p={} popsum={} spansum={} span8={} span16={} span32={} span64={} cons={} framed={}",
        COLD_TOTAL.load(Relaxed), COLD_PC1.load(Relaxed), COLD_PC2.load(Relaxed), COLD_PC3.load(Relaxed), COLD_PC4P.load(Relaxed),
        COLD_POPSUM.load(Relaxed), COLD_SPANSUM.load(Relaxed), COLD_SPAN8.load(Relaxed), COLD_SPAN16.load(Relaxed),
        COLD_SPAN32.load(Relaxed), COLD_SPAN64.load(Relaxed), COLD_CONS.load(Relaxed), COLD_FRAMED.load(Relaxed));
}
'''
assert anchor in s; s=s.replace(anchor,anchor+insert,1)

old='''        self.prune_env_cold(e, mask, slot)'''
new='''        COLD_TOTAL.fetch_add(1, Relaxed);
        let pc = u64::from(mask.count_ones());
        COLD_POPSUM.fetch_add(pc, Relaxed);
        match pc {
            1 => { COLD_PC1.fetch_add(1, Relaxed); }
            2 => { COLD_PC2.fetch_add(1, Relaxed); }
            3 => { COLD_PC3.fetch_add(1, Relaxed); }
            _ => { COLD_PC4P.fetch_add(1, Relaxed); }
        }
        let span = u64::from(64 - mask.leading_zeros());
        COLD_SPANSUM.fetch_add(span, Relaxed);
        if span <= 8 { COLD_SPAN8.fetch_add(1, Relaxed); }
        else if span <= 16 { COLD_SPAN16.fetch_add(1, Relaxed); }
        else if span <= 32 { COLD_SPAN32.fetch_add(1, Relaxed); }
        else { COLD_SPAN64.fetch_add(1, Relaxed); }
        match e {
            value::Env::Cons { .. } => { COLD_CONS.fetch_add(1, Relaxed); }
            value::Env::Framed { .. } => { COLD_FRAMED.fetch_add(1, Relaxed); }
            value::Env::Nil { .. } => {}
        }
        self.prune_env_cold(e, mask, slot)'''
assert old in s; p.write_text(s.replace(old,new,1))

p=Path('a2/src/main.rs'); s=p.read_text()
old='''    export_file.check_all_declars();
    // Pretty print as necessary'''
new='''    export_file.check_all_declars();
    sokonanoda::eval::dump_prune_shape_stats();
    // Pretty print as necessary'''
assert old in s; p.write_text(s.replace(old,new,1))
