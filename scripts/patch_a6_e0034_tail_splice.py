from pathlib import Path
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('--enabled', choices=('0','1'), required=True)
args = ap.parse_args()
enabled = args.enabled == '1'

p = Path('a6/src/eval.rs')
s = p.read_text()

marker = "pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert = marker + f"\nconst E0034_TAIL_SPLICE: bool = {'true' if enabled else 'false'};\n"
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
                    if rem & 1 != 0 {
                        buf[n].write(*v);
                        slots_hash = slots_hash
                            .wrapping_mul(0x9E3779B97F4A7C15)
                            .wrapping_add(*v as *const Value<'t> as usize as u64);
                        out_mask |= 1u64 << consumed;
                        n += 1;
                    }
                    let tail = rem >> 1;
                    if E0034_TAIL_SPLICE && tail != 0 {
                        let memo = match parent {
                            value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } => {
                                let (m, r) = prune.get();
                                if m == tail { r } else { None }
                            }
                            value::Env::Nil { .. } => None,
                        };
                        if let Some(hit) = memo {
                            match hit {
                                value::Env::Framed { mask: hm, slots: hs, .. } => {
                                    out_mask |= *hm << (consumed + 1);
                                    for sv in hs.iter().copied() {
                                        buf[n].write(sv);
                                        slots_hash = slots_hash
                                            .wrapping_mul(0x9E3779B97F4A7C15)
                                            .wrapping_add(sv as *const Value<'t> as usize as u64);
                                        n += 1;
                                    }
                                    break;
                                }
                                value::Env::Nil { .. } => break,
                                value::Env::Cons { .. } => {}
                            }
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
