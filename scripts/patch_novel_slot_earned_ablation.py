from pathlib import Path

# Same-lookup causal ablation for the opportunistic canonical-slot quotient.
#
# Perform the exact same is_canonical/canon_cache observations, but discard any
# earned representative and keep/hash the original raw slot. This isolates the
# benefit of compiling already-earned equivalence into frame identity from the
# cost/side effects of looking it up.

p = Path("a6/src/eval.rs")
s = p.read_text()

old = """                        let sv = slots[i];
                        buf[n].write(sv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(sv as *const Value<'t> as usize as u64);
"""
new = """                        let raw = slots[i];
                        let _earned = if raw.is_canonical() {
                            raw
                        } else {
                            let key = raw as *const Value<'t> as usize;
                            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(raw)
                        };
                        buf[n].write(raw);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(raw as *const Value<'t> as usize as u64);
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
                        let _earned = if raw.is_canonical() {
                            raw
                        } else {
                            let key = raw as *const Value<'t> as usize;
                            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(raw)
                        };
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
