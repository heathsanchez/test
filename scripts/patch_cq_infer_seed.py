from pathlib import Path

# V8: recurrence-gated, dependency-complete, closed type-result reuse.
#
# Existing raw type_cache remains first and authoritative.
# A 1024-entry expression-indexed seed table is consulted only after raw-cache
# miss. Exact dependency equality includes projected environment + the context
# types addressable by the expression. Reuse is allowed only for a closed result
# from identical infer/check mode and universe-check scope.

p=Path("a6/src/util.rs")
s=p.read_text()

const_marker="pub(crate) const PRUNE_DM_SHIFT: u32 = 64 - 10;\n"
const_insert=const_marker+"""
pub(crate) const CQ_INFER_SEED_LEN: usize = PRUNE_DM_LEN;
pub(crate) const CQ_INFER_SEED_SHIFT: u32 = PRUNE_DM_SHIFT;

#[derive(Clone, Copy)]
pub(crate) struct CqInferSeed<'a, 't> {
    pub(crate) expr: ExprPtr<'t>,
    pub(crate) env: E<'a>,
    pub(crate) ctx: crate::value::C<'a>,
    pub(crate) mode: u8,
    pub(crate) scope_key: u64,
    pub(crate) result: V<'a>,
}
"""
assert const_marker in s
s=s.replace(const_marker,const_insert,1)

field_marker="    pub(crate) type_cache: FxHashMap<(usize, ExprPtr<'t>), crate::infer::CachedType<'a>>,\n"
assert field_marker in s
s=s.replace(field_marker,field_marker+"    pub(crate) cq_infer_seed: Box<[Option<CqInferSeed<'a, 't>>; CQ_INFER_SEED_LEN]>,\n",1)

init_marker="            type_cache: session_fx_hash_map(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_infer_seed: Box::new([None; CQ_INFER_SEED_LEN]),\n",1)

clear_marker="        self.type_cache.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_infer_seed.fill(None);\n",1)

session_marker="        shrink_map(&mut self.type_cache);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        self.cq_infer_seed.fill(None);\n",1)
p.write_text(s)

p=Path("a6/src/infer.rs")
s=p.read_text()

impl_marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n    fn uparam_scope(&self) -> CheckScope<'t> {\n"
helpers="""impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn cq_infer_seed_rep(&self, v: V<'t>) -> V<'t> {
        if v.is_canonical() {
            v
        } else {
            let key = v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
        }
    }

    #[inline]
    fn cq_infer_seed_env_eq(&self, a: E<'t>, b: E<'t>) -> bool {
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
                        std::ptr::eq(self.cq_infer_seed_rep(*av), self.cq_infer_seed_rep(*bv))
                    })
            }
            _ => false,
        }
    }

    #[inline]
    fn cq_infer_seed_ctx_eq(&self, a: C<'t>, b: C<'t>, loose: u16) -> bool {
        if std::ptr::eq(a, b) {
            return true;
        }
        for i in 0..loose {
            let av = a.lookup(i);
            let bv = b.lookup(i);
            match (av, bv) {
                (Some(x), Some(y)) => {
                    if !std::ptr::eq(self.cq_infer_seed_rep(x), self.cq_infer_seed_rep(y)) {
                        return false;
                    }
                }
                (None, None) => {}
                _ => return false,
            }
        }
        true
    }

    #[inline]
    fn cq_infer_seed_mode_scope(&self, flag: InferFlag, scope: CheckScope<'t>) -> (u8, u64) {
        if flag == InferOnly {
            (0, 0)
        } else {
            let sk = match scope {
                CheckScope::Unchecked => 0,
                CheckScope::NoUparams => 1,
                CheckScope::Under(ls) => ls.get_hash().wrapping_add(2),
            };
            (1, sk)
        }
    }

    fn uparam_scope(&self) -> CheckScope<'t> {
"""
assert impl_marker in s
s=s.replace(impl_marker,helpers,1)

old="""        let key = (self.key_env(env, e) as *const value::Env<'t> as usize, e);
        let scope = self.uparam_scope();
        if let Some(cached) = self.tc_cache.type_cache.get(&key).copied() {
            if flag == InferOnly || cached.checked_under == scope {
                return cached.result;
            }
        }

        let r = match self.ctx.read_expr(e) {
"""
new="""        let te = self.key_env(env, e);
        let key = (te as *const value::Env<'t> as usize, e);
        let scope = self.uparam_scope();
        if let Some(cached) = self.tc_cache.type_cache.get(&key).copied() {
            if flag == InferOnly || cached.checked_under == scope {
                return cached.result;
            }
        }

        let (mode, scope_key) = self.cq_infer_seed_mode_scope(flag, scope);
        let expr_addr = e.as_ref() as *const Expr<'t> as usize as u64;
        let seed_slot = (
            expr_addr.wrapping_mul(0x9E3779B97F4A7C15)
            >> crate::util::CQ_INFER_SEED_SHIFT
        ) as usize;
        let loose = e.num_loose_bvars();

        if let Some(seed) = self.tc_cache.cq_infer_seed[seed_slot] {
            let exact = seed.expr == e
                && seed.mode == mode
                && seed.scope_key == scope_key
                && self.cq_infer_seed_env_eq(te, seed.env)
                && self.cq_infer_seed_ctx_eq(ctx, seed.ctx, loose);
            if exact {
                let result = std::hint::black_box(seed.result);
                if std::hint::black_box(result.is_closed()) {
                    let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
                    self.tc_cache.type_cache.insert(key, CachedType { result, checked_under });
                    return result;
                }
            }
        }

        let r = match self.ctx.read_expr(e) {
"""
assert old in s
s=s.replace(old,new,1)

old="""        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });
        r
"""
new="""        self.tc_cache.cq_infer_seed[seed_slot] = Some(crate::util::CqInferSeed {
            expr: e,
            env: te,
            ctx,
            mode,
            scope_key,
            result: r,
        });
        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });
        r
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
