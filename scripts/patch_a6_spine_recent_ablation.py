from pathlib import Path
import argparse,runpy,sys

ap=argparse.ArgumentParser()
ap.add_argument("--k",type=int,required=True,choices=[1,2,4,8,16])
args=ap.parse_args()

# Apply exact candidate with same K.
old_argv=sys.argv[:]
sys.argv=["patch_a6_spine_recent.py","--k",str(args.k)]
try:
    runpy.run_path("scripts/patch_a6_spine_recent.py",run_name="__main__")
finally:
    sys.argv=old_argv

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""        if let Some(s) = recent_hit {
            let pos = self.tc_cache.spine_recent_pos;
            self.tc_cache.spine_recent[pos] = Some((key.0, key.1, s));
            self.tc_cache.spine_recent_pos = (pos + 1) & (crate::util::SPINE_RECENT_LEN - 1);
            return s;
        }

        let arena = self.arena;
"""
new="""        if let Some(s) = recent_hit {
            let _recent_hit = std::hint::black_box(s);
        }

        let arena = self.arena;
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
