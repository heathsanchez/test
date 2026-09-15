from pathlib import Path
import runpy

# V7 ablation: exact same recurrence seed, exact env comparison, closedness test,
# and seed replacement, but recompute even on an exact closed hit.
runpy.run_path("scripts/patch_cq_pi_recurrence_seed.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""                        if closed {
                            let ce = self.key_env(te, e);
                            let v = value::mk_pi(
                                self.arena,
                                binder_name,
                                binder_style,
                                domain,
                                Closure::mk_eval(ce, body),
                            );
                            self.tc_cache.open_eval_cache.insert(key, v);
                            return v;
                        }
"""
new="""                        if closed {
                            let _cached_domain = std::hint::black_box(domain);
                        }
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
