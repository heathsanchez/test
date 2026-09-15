from pathlib import Path
import runpy

# V6: apply exact V5 direct-map mechanism, but only reuse a cached domain if
# that domain is closed. Open cached domains are observed but recomputed.
runpy.run_path("scripts/patch_cq_pi_domain_dm.py", run_name="__main__")

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""                    if let Some(domain) = hit {
                        let domain = std::hint::black_box(domain);
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

                    let domain = self.eval(depth, te, binder_type);
"""
new="""                    if let Some(domain) = hit {
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
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
