from pathlib import Path

# Same-cost causal ablation for the canonical-slot quotient.
#
# Pay the same canonicalize_for_spine() calls and therefore share their cache
# side effects, but discard the canonical representatives and keep the original
# raw slots in projected frames. Difference from the quotient arm is therefore
# whether the discovered equivalence is compiled into frame representation.

p = Path("a6/src/eval.rs")
s = p.read_text()

old = """                        let sv = slots[i];
                        buf[n].write(sv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(sv as *const Value<'t> as usize as u64);
"""
new = """                        let sv = slots[i];
                        let _canonical = self.canonicalize_for_spine(sv);
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
                        let raw = *v;
                        let _canonical = self.canonicalize_for_spine(raw);
                        buf[n].write(raw);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(raw as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
"""
assert old in s
s = s.replace(old, new, 1)

p.write_text(s)
