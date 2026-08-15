from pathlib import Path

# Assumes a3 has already been reconstructed from 9b4ea12 + E0018.
p = Path('a3/src/eval.rs')
s = p.read_text()
s = s.replace('use std::cell::OnceCell;\n', 'use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n', 1)
marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + "\nstatic FRAME_INTERN_CALLS: AtomicU64 = AtomicU64::new(0);\nstatic FRAME_INTERN_HITS: AtomicU64 = AtomicU64::new(0);\nstatic FRAME_INTERN_MISSES: AtomicU64 = AtomicU64::new(0);\n\npub fn print_frame_intern_stats() {\n    eprintln!(\"FRAME_INTERN_STATS calls={} hits={} misses={}\",\n        FRAME_INTERN_CALLS.load(Relaxed), FRAME_INTERN_HITS.load(Relaxed), FRAME_INTERN_MISSES.load(Relaxed));\n}\n"
assert marker in s
s = s.replace(marker, insert, 1)
old = """    fn intern_frame(
        &mut self,
        hash: u64,
        mask: u64,
        slots: &[V<'t>],
        lsub: Option<&'t value::LevelSub<'t>>,
    ) -> E<'t> {
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        if let Some(e) = self.tc_cache.frames.find(hash, |e: &E<'t>| match e {
"""
new = """    fn intern_frame(
        &mut self,
        hash: u64,
        mask: u64,
        slots: &[V<'t>],
        lsub: Option<&'t value::LevelSub<'t>>,
    ) -> E<'t> {
        FRAME_INTERN_CALLS.fetch_add(1, Relaxed);
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        if let Some(e) = self.tc_cache.frames.find(hash, |e: &E<'t>| match e {
"""
assert old in s
s = s.replace(old,new,1)
old = """        }) {
            return e;
        }
        let len = 64 - mask.leading_zeros();
"""
new = """        }) {
            FRAME_INTERN_HITS.fetch_add(1, Relaxed);
            return e;
        }
        FRAME_INTERN_MISSES.fetch_add(1, Relaxed);
        let len = 64 - mask.leading_zeros();
"""
assert old in s
s = s.replace(old,new,1)
p.write_text(s)

p = Path('a3/src/main.rs')
s = p.read_text()
old = """    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
new = """    if std::env::var_os(\"SOKONANODA_FRAME_DIAG\").is_some() {
        sokonanoda::eval::print_frame_intern_stats();
    }
    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
