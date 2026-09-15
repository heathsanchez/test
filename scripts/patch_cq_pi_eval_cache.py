from pathlib import Path

# V3: consequential Pi cache.
#
# Shadow diagnostic run 34915583025 observed 602 held-out raw open-eval cache
# misses that would hit under the already-earned consequential environment
# signature. Every observed opportunity was a Pi evaluation.
#
# Keep raw Env objects unchanged. Keep the existing pointer-keyed open_eval_cache
# unchanged. On a pointer-cache miss for Pi only, consult a secondary cache keyed
# by (Pi expression, projected mask, level-sub identity, already-earned canonical
# slot representatives). No eager canonicalization is performed.

p=Path("a6/src/util.rs")
s=p.read_text()

field_marker="    pub(crate) open_eval_cache: FxHashMap<(usize, ExprPtr<'t>), V<'a>>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_pi_eval_cache: "
    "FxHashMap<(ExprPtr<'t>, u64, usize, Vec<usize>), V<'a>>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            open_eval_cache: session_fx_hash_map(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_pi_eval_cache: session_fx_hash_map(),\n",1)

clear_marker="        self.open_eval_cache.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_pi_eval_cache.clear();\n",1)

session_marker="        shrink_map(&mut self.open_eval_cache);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_map(&mut self.cq_pi_eval_cache);\n",1)

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

            // Consequential identity is intentionally separate from operational
            // Env identity. Restrict to Pi because the frozen shadow diagnostic
            // found all cross-identity reuse opportunities there.
            let pi_qkey = if matches!(self.ctx.read_expr_ref(e), Expr::Pi { .. }) {
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
                Some((e, smask, slsub, sslots))
            } else {
                None
            };

            if let Some(qkey) = pi_qkey.as_ref() {
                if let Some(v) = self.tc_cache.cq_pi_eval_cache.get(qkey) {
                    return v;
                }
            }

            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            if let Some(qkey) = pi_qkey {
                self.tc_cache.cq_pi_eval_cache.insert(qkey, v);
            }
            return v;
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
