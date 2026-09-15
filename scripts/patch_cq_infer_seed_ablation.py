from pathlib import Path
import runpy

# Matched ablation for V8.
# Apply exact candidate machinery, but when an exact closed seed hit exists,
# consume it through the same black-box boundary and deliberately recompute.

runpy.run_path("scripts/patch_cq_infer_seed.py", run_name="__main__")

p=Path("a6/src/infer.rs")
s=p.read_text()

old="""            if exact {
                let result = std::hint::black_box(seed.result);
                if std::hint::black_box(result.is_closed()) {
                    let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
                    self.tc_cache.type_cache.insert(key, CachedType { result, checked_under });
                    return result;
                }
            }
"""
new="""            if exact {
                let result = std::hint::black_box(seed.result);
                if std::hint::black_box(result.is_closed()) {
                    let _cached_result = std::hint::black_box(result);
                }
            }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
