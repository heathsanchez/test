from pathlib import Path

# Diagnostic only. Assumes `a6` was reconstructed with scripts/patch_a6.py.
p = Path('a6/src/eval.rs')
s = p.read_text()

s = s.replace(
    'use std::cell::OnceCell;\n',
    'use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n',
    1,
)

marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + r'''

static E0032_COLD_CALLS: AtomicU64 = AtomicU64::new(0);
static E0032_CONS_SCANNED: AtomicU64 = AtomicU64::new(0);
static E0032_CONS_SELECTED: AtomicU64 = AtomicU64::new(0);
static E0032_CONS_SKIPPED: AtomicU64 = AtomicU64::new(0);
static E0032_FRAMED_CALLS: AtomicU64 = AtomicU64::new(0);
static E0032_SELECTED_SLOTS: AtomicU64 = AtomicU64::new(0);
static E0032_MAX_CONS_SCAN: AtomicU64 = AtomicU64::new(0);

pub fn print_e0032_stats() {
    eprintln!(
        "E0032_STATS cold_calls={} cons_scanned={} cons_selected={} cons_skipped={} framed_calls={} selected_slots={} max_cons_scan={}",
        E0032_COLD_CALLS.load(Relaxed),
        E0032_CONS_SCANNED.load(Relaxed),
        E0032_CONS_SELECTED.load(Relaxed),
        E0032_CONS_SKIPPED.load(Relaxed),
        E0032_FRAMED_CALLS.load(Relaxed),
        E0032_SELECTED_SLOTS.load(Relaxed),
        E0032_MAX_CONS_SCAN.load(Relaxed),
    );
}
'''
assert marker in s
s = s.replace(marker, insert, 1)

old = """    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {
        let mut buf: [std::mem::MaybeUninit<V<'t>>; 64] = [const { std::mem::MaybeUninit::uninit() }; 64];
"""
new = """    fn prune_env_cold(&mut self, e: E<'t>, mask: u64, slot: usize) -> E<'t> {
        E0032_COLD_CALLS.fetch_add(1, Relaxed);
        let mut local_cons_scan = 0u64;
        let mut buf: [std::mem::MaybeUninit<V<'t>>; 64] = [const { std::mem::MaybeUninit::uninit() }; 64];
"""
assert old in s
s = s.replace(old, new, 1)

old = """                value::Env::Framed { mask: fmask, slots, .. } => {
                    let limit = 64 - consumed;
"""
new = """                value::Env::Framed { mask: fmask, slots, .. } => {
                    E0032_FRAMED_CALLS.fetch_add(1, Relaxed);
                    let limit = 64 - consumed;
"""
assert old in s
s = s.replace(old, new, 1)

old = """                value::Env::Cons { v, parent, .. } => {
                    if rem & 1 != 0 {
                        buf[n].write(*v);
"""
new = """                value::Env::Cons { v, parent, .. } => {
                    E0032_CONS_SCANNED.fetch_add(1, Relaxed);
                    local_cons_scan += 1;
                    if rem & 1 != 0 {
                        E0032_CONS_SELECTED.fetch_add(1, Relaxed);
                        buf[n].write(*v);
"""
assert old in s
s = s.replace(old, new, 1)

old = """                        n += 1;
                    }
                    rem >>= 1;
"""
new = """                        n += 1;
                    } else {
                        E0032_CONS_SKIPPED.fetch_add(1, Relaxed);
                    }
                    rem >>= 1;
"""
assert old in s
s = s.replace(old, new, 1)

old = """        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
"""
new = """        E0032_SELECTED_SLOTS.fetch_add(n as u64, Relaxed);
        E0032_MAX_CONS_SCAN.fetch_max(local_cons_scan, Relaxed);
        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
"""
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)

p = Path('a6/src/main.rs')
s = p.read_text()
old = """    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
new = """    if std::env::var_os(\"SOKONANODA_E0032_DIAG\").is_some() {
        sokonanoda::eval::print_e0032_stats();
    }
    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
