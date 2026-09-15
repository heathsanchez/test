from pathlib import Path

# V5: bounded direct-mapped consequential Pi-domain cache.
#
# Same consequential equality as V4, but no Vec key allocation and no general
# hash map. A semantic hash selects one of 1024 entries (the checker already uses
# a 1024-entry prune direct map). Before reuse, exact mask/lsub/slot equality
# under already-earned canonical representatives is checked.
#
# Hash collisions can only miss/replace; they cannot authorize reuse.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
const_insert=const_marker+"""
pub(crate) const CQ_PI_DM_LEN: usize = PRUNE_DM_LEN;
pub(crate) const CQ_PI_DM_SHIFT: u32 = PRUNE_DM_SHIFT;

#[derive(Clone, Copy)]
pub(crate) struct CqPiDmEntry<'a, 't> {
    pub(crate) hash: u64,
    pub(crate) expr: ExprPtr<'t>,
    pub(crate) env: E<'a>,
    pub(crate) domain: V<'a>,
}
"""
assert const_marker in s
s=s.replace(const_marker,const_insert,1)

field_marker="    pub(crate) open_eval_cache: FxHashMap<(usize, ExprPtr<'t>), V<'a>>,\n"
field_insert=field_marker+"    pub(crate) cq_pi_dm: Box<[Option<CqPiDmEntry<'a, 't>>; CQ_PI_DM_LEN]>,\n"
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            open_eval_cache: session_fx_hash_map(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_pi_dm: Box::new([None; CQ_PI_DM_LEN]),\n",1)

clear_marker="        self.open_eval_cache.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_pi_dm.fill(None);\n",1)

session_marker="        shrink_map(&mut self.open_eval_cache);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        self.cq_pi_dm.fill(None);\n",1)

p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

impl_marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n    pub(crate) fn eval(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {\n"
helpers="""impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn cq_earned_rep(&self, v: V<'t>) -> V<'t> {
        if v.is_canonical() {
            v
        } else {
            let key = v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
        }
    }

    #[inline]
    fn cq_env_hash(&self, env: E<'t>) -> Option<u64> {
        let lsub = env.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize as u64);
        let mut h = match env {
            value::Env::Nil { .. } => 0xA0761D6478BD642F_u64,
            value::Env::Framed { mask, .. } =>
                mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(0xE7037ED1A0B428DB),
            value::Env::Cons { .. } => return None,
        };
        h = h.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(lsub);
        if let value::Env::Framed { slots, .. } = env {
            for v in slots.iter() {
                let rep = self.cq_earned_rep(*v);
                h = h
                    .wrapping_mul(0xD6E8FEB86659FD93)
                    .wrapping_add(rep as *const Value<'t> as usize as u64);
            }
        }
        Some(h)
    }

    #[inline]
    fn cq_env_eq(&self, a: E<'t>, b: E<'t>) -> bool {
        if std::ptr::eq(a, b) {
            return true;
        }
        let al = a.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let bl = b.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        if al != bl {
            return false;
        }
        match (a, b) {
            (value::Env::Nil { .. }, value::Env::Nil { .. }) => true,
            (
                value::Env::Framed { mask: am, slots: aslots, .. },
                value::Env::Framed { mask: bm, slots: bslots, .. },
            ) => {
                *am == *bm
                    && aslots.len() == bslots.len()
                    && aslots.iter().zip(bslots.iter()).all(|(av, bv)| {
                        std::ptr::eq(self.cq_earned_rep(*av), self.cq_earned_rep(*bv))
                    })
            }
            _ => false,
        }
    }

    pub(crate) fn eval(&mut self, depth: u32, env: E<'t>, e: ExprPtr<'t>) -> V<'t> {
"""
assert impl_marker in s
s=s.replace(impl_marker,helpers,1)

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
                if let Some(ehash) = self.cq_env_hash(te) {
                    let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
                    let selector = ehash ^ expr_addr.wrapping_mul(0x9E3779B97F4A7C15);
                    let slot = (selector >> crate::util::CQ_PI_DM_SHIFT) as usize;
                    let hit = match self.tc_cache.cq_pi_dm[slot] {
                        Some(ent) =>
                            ent.hash == ehash
                                && ent.expr == e
                                && self.cq_env_eq(te, ent.env)
                                .then_some(ent.domain),
                        None => None,
                    };
                    if let Some(domain) = hit {
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
                    let ce = self.key_env(te, e);
                    let v = value::mk_pi(
                        self.arena,
                        binder_name,
                        binder_style,
                        domain,
                        Closure::mk_eval(ce, body),
                    );
                    self.tc_cache.cq_pi_dm[slot] = Some(crate::util::CqPiDmEntry {
                        hash: ehash,
                        expr: e,
                        env: te,
                        domain,
                    });
                    self.tc_cache.open_eval_cache.insert(key, v);
                    return v;
                }
            }

            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            return v;
"""
# Correct a precedence-sensitive fragment after replacement below.
assert old in s
s=s.replace(old,new,1)
# Rust's bool::then_some must apply to the full exact-equality predicate.
s=s.replace(
"""                        Some(ent) =>
                            ent.hash == ehash
                                && ent.expr == e
                                && self.cq_env_eq(te, ent.env)
                                .then_some(ent.domain),
""",
"""                        Some(ent) => {
                            let exact = ent.hash == ehash
                                && ent.expr == e
                                && self.cq_env_eq(te, ent.env);
                            exact.then_some(ent.domain)
                        }
""",
1)
p.write_text(s)
