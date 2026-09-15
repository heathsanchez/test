from pathlib import Path

# Opportunistic canonical-slot quotient.
#
# RED run 34914346859 found 2,983 projected-frame false splits that can be
# eliminated using canonical representatives ALREADY earned by normal checker
# execution. This patch never invokes canonicalize_for_spine() from
# prune_env_cold.
#
# For a selected slot:
#   - if already canonical, keep it;
#   - else, if canon_cache already maps this raw value to a representative,
#     use that representative;
#   - otherwise keep it raw.
#
# Therefore acquisition cost is not paid on the projection path.

p = Path("a6/src/eval.rs")
s = p.read_text()

old = """                        let sv = slots[i];
                        buf[n].write(sv);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(sv as *const Value<'t> as usize as u64);
"""
new = """                        let raw = slots[i];
                        let sv = if raw.is_canonical() {
                            raw
                        } else {
                            let key = raw as *const Value<'t> as usize;
                            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(raw)
                        };
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
                        let cv = if raw.is_canonical() {
                            raw
                        } else {
                            let key = raw as *const Value<'t> as usize;
                            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(raw)
                        };
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
