from pathlib import Path

# Discovery-only arm for the consequence-quotient demo.
#
# It deliberately DOES NOT reuse equal frames. Instead it keeps one canonical
# representative only as a diagnostic index, counts later requests with the
# same consequential frame signature, and returns a fresh frame for every hit.
# This lets discovery observe candidate equivalence before the quotient is
# compiled into reuse.

p = Path("a6/src/eval.rs")
s = p.read_text()

s = s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)

marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + """
static CQ_DISCOVERY_CALLS: AtomicU64 = AtomicU64::new(0);
static CQ_DISCOVERY_REPEAT_SIGNATURES: AtomicU64 = AtomicU64::new(0);
static CQ_DISCOVERY_NEW_SIGNATURES: AtomicU64 = AtomicU64::new(0);

pub fn print_consequence_quotient_discovery() {
    eprintln!(
        "CQ_DISCOVERY calls={} repeat_signatures={} new_signatures={}",
        CQ_DISCOVERY_CALLS.load(Relaxed),
        CQ_DISCOVERY_REPEAT_SIGNATURES.load(Relaxed),
        CQ_DISCOVERY_NEW_SIGNATURES.load(Relaxed)
    );
}
"""
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
            value::Env::Framed { mask: m, slots: sl, lsub: l, .. } =>
                *m == mask
                    && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                    && sl.len() == slots.len()
                    && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b)),
            _ => false,
        }) {
            return e;
        }
        let len = 64 - mask.leading_zeros();
        let e: E<'t> = self.arena.alloc(value::Env::Framed {
            mask,
            slots: self.arena.alloc_slice_copy(slots),
            lsub,
            hash,
            len,
            prune: std::cell::Cell::new((0, None)),
        });
        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        e
    }
"""

new = """    fn intern_frame(
        &mut self,
        hash: u64,
        mask: u64,
        slots: &[V<'t>],
        lsub: Option<&'t value::LevelSub<'t>>,
    ) -> E<'t> {
        CQ_DISCOVERY_CALLS.fetch_add(1, Relaxed);
        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);

        // The table is diagnostic only in this arm. A matching representative
        // proves that this exact projected frame signature has been requested
        // before, but we intentionally return a fresh equal frame so no reuse
        // benefit can leak into discovery.
        if self.tc_cache.frames.find(hash, |e: &E<'t>| match e {
            value::Env::Framed { mask: m, slots: sl, lsub: l, .. } =>
                *m == mask
                    && l.map_or(0, |l| l as *const value::LevelSub<'t> as usize) == lsub_addr
                    && sl.len() == slots.len()
                    && sl.iter().zip(slots).all(|(a, b)| std::ptr::eq(*a, *b)),
            _ => false,
        }).is_some() {
            CQ_DISCOVERY_REPEAT_SIGNATURES.fetch_add(1, Relaxed);
            let len = 64 - mask.leading_zeros();
            return self.arena.alloc(value::Env::Framed {
                mask,
                slots: self.arena.alloc_slice_copy(slots),
                lsub,
                hash,
                len,
                prune: std::cell::Cell::new((0, None)),
            });
        }

        CQ_DISCOVERY_NEW_SIGNATURES.fetch_add(1, Relaxed);
        let len = 64 - mask.leading_zeros();
        let e: E<'t> = self.arena.alloc(value::Env::Framed {
            mask,
            slots: self.arena.alloc_slice_copy(slots),
            lsub,
            hash,
            len,
            prune: std::cell::Cell::new((0, None)),
        });
        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        e
    }
"""

assert old in s
s = s.replace(old, new, 1)
p.write_text(s)

p = Path("a6/src/main.rs")
s = p.read_text()
old = """    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new = """    if std::env::var_os("SOKONANODA_CQ_DISCOVERY").is_some() {
        sokonanoda::eval::print_consequence_quotient_discovery();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old, new, 1))
