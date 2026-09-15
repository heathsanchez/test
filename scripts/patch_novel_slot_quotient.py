from pathlib import Path

# Novel canonical-slot quotient.
#
# RED evidence (run 34913712534) showed 5,317 cases on the frozen discovery
# workload where distinct raw projected-slot vectors collapse to the same
# representation under the checker's existing canonicalize_for_spine().
#
# Minimal repair: canonicalize a slot only when it is selected into a projected
# frame, before frame hashing/interning. No new equality relation is invented;
# this composes the checker's already-admitted value canonicalization with its
# already-admitted frame interning.

p = Path("a6/src/eval.rs")
s = p.read_text()

old = """                        let sv = slots[i];
                        buf[n].write(sv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(sv as *const Value<'t> as usize as u64);
"""
new = """                        let sv = self.canonicalize_for_spine(slots[i]);
                        buf[n].write(sv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(sv as *const Value<'t> as usize as u64);
"""
assert old in s
s = s.replace(old, new, 1)

old = """                    if rem & 1 != 0 {
                        buf[n].write(*v);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(*v as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
"""
new = """                    if rem & 1 != 0 {
                        let cv = self.canonicalize_for_spine(*v);
                        buf[n].write(cv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(cv as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s)
