from pathlib import Path
import runpy

# V6 ablation: exact same direct-map lookup and closedness test, but even a
# closed hit is deliberately recomputed.
runpy.run_path("scripts/patch_cq_pi_closed_domain_dm.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""                    if let Some(domain) = hit {
                        let domain = std::hint::black_box(domain);
                        let closed = std::hint::black_box(domain.is_closed());
                        if closed {
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
                    }

                    let domain = self.eval(depth, te, binder_type);
"""
new="""                    if let Some(domain) = hit {
                        let domain = std::hint::black_box(domain);
                        let closed = std::hint::black_box(domain.is_closed());
                        if closed {
                            let _cached_domain = std::hint::black_box(domain);
                        }
                    }

                    let domain = self.eval(depth, te, binder_type);
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
