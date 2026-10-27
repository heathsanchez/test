#!/usr/bin/env python3
"""Instrument exact Nucleus conversion context-copy sites (diagnostics only).

Must run in the root of a clean heathsanchez/test checkout at ff003e7.
Source semantics are unchanged. Added counters are diagnostic evidence, not
permission to quotient capture environments.
"""
from pathlib import Path
import subprocess
import sys

PIN = "ff003e7fad888d39a40cfd2375885fe20e3209fa"
if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != PIN:
    sys.exit("Refusing to patch: checkout is not qualified Nucleus commit " + PIN)
source = Path("metatron-kernel/src/convert.rs")
main = Path("metatron-kernel/src/main.rs")
s = source.read_text()
m = main.read_text()
assert "nucleus_context_copy" not in s, "Already instrumented"
needle = "context.to_vec()"
count = s.count(needle)
if count != 7:
    sys.exit(f"Refusing patch: expected exactly 7 context copy sites, got {count}")

# This counts exactly the seven current call sites, with separate per-site data.
for site in range(7):
    s = s.replace(needle, f"nucleus_context_copy(context, {site})", 1)
block = '''
// Diagnostic-only context-copy census. The same Vec clone remains authoritative;
// all semantic judgments, binder identities and original levels are untouched.
#[cfg(feature = "diagnostics")]
thread_local! {
    static NUCLEUS_CONTEXT_COUNTS: std::cell::Cell<([u64; 7], [u64; 7], [u64; 7])> =
        const { std::cell::Cell::new(([0; 7], [0; 7], [0; 7])) };
}
#[inline]
fn nucleus_context_copy(context: &[TypeValue], site: usize) -> Vec<TypeValue> {
    #[cfg(feature = "diagnostics")]
    NUCLEUS_CONTEXT_COUNTS.with(|counter| {
        let (mut copies, mut slots, mut widest) = counter.get();
        let w = context.len() as u64;
        copies[site] = copies[site].saturating_add(1);
        slots[site] = slots[site].saturating_add(w);
        widest[site] = widest[site].max(w);
        counter.set((copies, slots, widest));
    });
    #[cfg(not(feature = "diagnostics"))]
    let _ = site;
    context.to_vec()
}
#[cfg(feature = "diagnostics")]
pub fn context_copy_census() -> ([u64; 7], [u64; 7], [u64; 7]) {
    NUCLEUS_CONTEXT_COUNTS.with(|counter| counter.get())
}
'''
marker = "type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue);"
assert s.count(marker) == 1
s = s.replace(marker, block + "\n" + marker, 1)
needle_main = '        let run = metatron_kernel::run_with_diagnostics(BufReader::new(io::stdin().lock()));'
assert m.count(needle_main) == 1
m = m.replace(needle_main, needle_main + '''
        let (copies, slots, widest) = metatron_kernel::convert::context_copy_census();
        eprintln!(
            "NUCLEUS_CONTEXT_COST_JSON:{{\\"copy_sites\\":7,\\"copies_by_site\\":{:?},\\"slots_by_site\\":{:?},\\"widest_by_site\\":{:?}}}",
            copies, slots, widest,
        );''')
source.write_text(s)
main.write_text(m)
print("Instrumented seven verified context copy sites, with no semantic changes.")
