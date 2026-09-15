from pathlib import Path
import runpy

# Same-front-lookup ablation. Apply the exact production front-cache data
# structure and key/index logic, but deliberately never return a front hit.
# This controls front-array allocation, hashing, exact comparison, and updates.

runpy.run_path("scripts/patch_a6_spine_front.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""        if let Some((kp, ke, s)) = self.tc_cache.spine_front[front_i] {
            if kp == key.0 && ke == key.1 {
                return s;
            }
        }

        let arena = self.arena;
"""
new="""        if let Some((kp, ke, s)) = self.tc_cache.spine_front[front_i] {
            if kp == key.0 && ke == key.1 {
                let _front_hit = std::hint::black_box(s);
            }
        }

        let arena = self.arena;
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
