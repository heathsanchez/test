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

static E0033_CONS_STEPS: AtomicU64 = AtomicU64::new(0);
static E0033_TAIL_NONZERO: AtomicU64 = AtomicU64::new(0);
static E0033_PARENT_MEMO_MATCH: AtomicU64 = AtomicU64::new(0);
static E0033_PARENT_MEMO_RESULT: AtomicU64 = AtomicU64::new(0);
static E0033_PARENT_FRAMED: AtomicU64 = AtomicU64::new(0);
static E0033_PARENT_CONS: AtomicU64 = AtomicU64::new(0);

pub fn print_e0033_stats() {
    eprintln!(
        "E0033_STATS cons_steps={} tail_nonzero={} parent_memo_match={} parent_memo_result={} parent_framed={} parent_cons={}",
        E0033_CONS_STEPS.load(Relaxed),
        E0033_TAIL_NONZERO.load(Relaxed),
        E0033_PARENT_MEMO_MATCH.load(Relaxed),
        E0033_PARENT_MEMO_RESULT.load(Relaxed),
        E0033_PARENT_FRAMED.load(Relaxed),
        E0033_PARENT_CONS.load(Relaxed),
    );
}
'''
assert marker in s
s = s.replace(marker, insert, 1)

old = """                value::Env::Cons { v, parent, .. } => {
                    if rem & 1 != 0 {
                        buf[n].write(*v);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(*v as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
                    rem >>= 1;
                    if rem == 0 {
                        break;
                    }
                    consumed += 1;
                    cur = parent;
                }
"""
new = """                value::Env::Cons { v, parent, .. } => {
                    E0033_CONS_STEPS.fetch_add(1, Relaxed);
                    if rem & 1 != 0 {
                        buf[n].write(*v);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(*v as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
                    let tail = rem >> 1;
                    if tail != 0 {
                        E0033_TAIL_NONZERO.fetch_add(1, Relaxed);
                        match parent {
                            value::Env::Cons { prune, .. } => {
                                E0033_PARENT_CONS.fetch_add(1, Relaxed);
                                let (m, r) = prune.get();
                                if m == tail {
                                    E0033_PARENT_MEMO_MATCH.fetch_add(1, Relaxed);
                                    if r.is_some() { E0033_PARENT_MEMO_RESULT.fetch_add(1, Relaxed); }
                                }
                            }
                            value::Env::Framed { prune, .. } => {
                                E0033_PARENT_FRAMED.fetch_add(1, Relaxed);
                                let (m, r) = prune.get();
                                if m == tail {
                                    E0033_PARENT_MEMO_MATCH.fetch_add(1, Relaxed);
                                    if r.is_some() { E0033_PARENT_MEMO_RESULT.fetch_add(1, Relaxed); }
                                }
                            }
                            value::Env::Nil { .. } => {}
                        }
                    }
                    rem = tail;
                    if rem == 0 {
                        break;
                    }
                    consumed += 1;
                    cur = parent;
                }
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
new = """    if std::env::var_os(\"SOKONANODA_E0033_DIAG\").is_some() {
        sokonanoda::eval::print_e0033_stats();
    }
    match out {
        Ok(Some(msg)) => println!(\"{}\", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
