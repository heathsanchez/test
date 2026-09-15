from pathlib import Path

# V4: consequential Pi-domain cache with operational rebinding.
#
# Keep raw Env identity and the existing open_eval_cache unchanged.
# On a pointer-cache miss for Pi:
#   1. construct the same already-earned consequential environment key;
#   2. if a domain is cached, reuse only that domain;
#   3. rebuild Value::Pi with a body Closure bound to the CURRENT raw env.
#
# No whole Pi value is shared across raw environments.
# No eager canonicalization is performed.

p=Path("a6/src/util.rs")
s=p.read_text()

field_marker="    pub(crate) open_eval_cache: FxHashMap<(usize, ExprPtr<'t>), V<'a>>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_pi_domain_cache: "
    "FxHashMap<(ExprPtr<'t>, u64, usize, Vec<usize>), V<'a>>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            open_eval_cache: session_fx_hash_map(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_pi_domain_cache: session_fx_hash_map(),\n",1)

clear_marker="        self.open_eval_cache.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_pi_domain_cache.clear();\n",1)

session_marker="        shrink_map(&mut self.open_eval_cache);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_map(&mut self.cq_pi_domain_cache);\n",1)

p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }
            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            return v;
"""
new="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }

            let pi_data = match self.ctx.read_expr_ref(e) {
                &Expr::Pi { binder_name, binder_style, binder_type, body, .. } =>
                    Some((binder_name, binder_style, binder_type, body)),
                _ => None,
            };

            if let Some((binder_name, binder_style, binder_type, body)) = pi_data {
                let (smask, slsub, sslots): (u64, usize, Vec<usize>) = match te {
                    value::Env::Framed { mask, slots, .. } => {
                        let ps = slots.iter().map(|v| {
                            let raw = *v;
                            let rep = if raw.is_canonical() {
                                raw
                            } else {
                                let k = raw as *const Value<'t> as usize;
                                self.tc_cache.canon_cache.get(&k).copied().unwrap_or(raw)
                            };
                            rep as *const Value<'t> as usize
                        }).collect();
                        (*mask, te.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize), ps)
                    }
                    value::Env::Nil { .. } =>
                        (0, te.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize), Vec::new()),
                    value::Env::Cons { .. } =>
                        (u64::MAX, te as *const value::Env<'t> as usize, Vec::new()),
                };
                let qkey = (e, smask, slsub, sslots);

                if let Some(domain) = self.tc_cache.cq_pi_domain_cache.get(&qkey).copied() {
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

                // Same semantics as eval_no_cache's Pi arm, but retain the
                // reusable domain consequence for future equivalent raw envs.
                let domain = self.eval(depth, te, binder_type);
                let ce = self.key_env(te, e);
                let v = value::mk_pi(
                    self.arena,
                    binder_name,
                    binder_style,
                    domain,
                    Closure::mk_eval(ce, body),
                );
                self.tc_cache.cq_pi_domain_cache.insert(qkey, domain);
                self.tc_cache.open_eval_cache.insert(key, v);
                return v;
            }

            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            return v;
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
