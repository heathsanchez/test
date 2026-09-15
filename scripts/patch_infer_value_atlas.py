from pathlib import Path

# Diagnostic-only Consequence Value Atlas for type inference.
#
# Existing type_cache remains untouched and authoritative.
# On a real raw-key cache miss, construct a dependency-complete shadow identity:
#   expression
#   inference/check mode + universe scope
#   projected environment (mask, lsub, already-earned representatives)
#   exactly the local context types addressable by the expression's loose bvars
#
# A repeat shadow signature is only measured; no result is reused.

p=Path("a6/src/util.rs")
s=p.read_text()

field_marker="    pub(crate) type_cache: FxHashMap<(usize, ExprPtr<'t>), crate::infer::CachedType<'a>>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_infer_shadow: "
    "FxHashSet<(ExprPtr<'t>, u8, u64, u64, usize, Vec<usize>, Vec<usize>)>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            type_cache: session_fx_hash_map(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_infer_shadow: FxHashSet::default(),\n",1)

clear_marker="        self.type_cache.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_infer_shadow.clear();\n",1)

session_marker="        shrink_map(&mut self.type_cache);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_set(&mut self.cq_infer_shadow);\n",1)
p.write_text(s)

p=Path("a6/src/infer.rs")
s=p.read_text()

s=s.replace(
    "use InferFlag::*;\n",
    "use InferFlag::*;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nuse std::time::Instant;\n",
    1,
)

marker="#[derive(Debug, Clone, Copy)]\npub(crate) struct CachedType<'a> {\n"
stats="""static IVA_INFER_CALLS: AtomicU64 = AtomicU64::new(0);
static IVA_MISSES: AtomicU64 = AtomicU64::new(0);
static IVA_REPEATS: AtomicU64 = AtomicU64::new(0);
static IVA_REPEAT_INFER_CALLS: AtomicU64 = AtomicU64::new(0);
static IVA_MAX_INFER_CALLS: AtomicU64 = AtomicU64::new(0);
static IVA_REPEAT_NS: AtomicU64 = AtomicU64::new(0);
static IVA_MAX_NS: AtomicU64 = AtomicU64::new(0);
static IVA_CLOSED_RESULTS: AtomicU64 = AtomicU64::new(0);
static IVA_APP: AtomicU64 = AtomicU64::new(0);
static IVA_LAMBDA: AtomicU64 = AtomicU64::new(0);
static IVA_PI: AtomicU64 = AtomicU64::new(0);
static IVA_LET: AtomicU64 = AtomicU64::new(0);
static IVA_PROJ: AtomicU64 = AtomicU64::new(0);
static IVA_C1: AtomicU64 = AtomicU64::new(0);
static IVA_C2_4: AtomicU64 = AtomicU64::new(0);
static IVA_C5_16: AtomicU64 = AtomicU64::new(0);
static IVA_C17_64: AtomicU64 = AtomicU64::new(0);
static IVA_C65P: AtomicU64 = AtomicU64::new(0);

#[inline]
fn iva_record_calls(cost: u64) {
    IVA_REPEAT_INFER_CALLS.fetch_add(cost, Relaxed);
    IVA_MAX_INFER_CALLS.fetch_max(cost, Relaxed);
    match cost {
        0 | 1 => { IVA_C1.fetch_add(1, Relaxed); }
        2..=4 => { IVA_C2_4.fetch_add(1, Relaxed); }
        5..=16 => { IVA_C5_16.fetch_add(1, Relaxed); }
        17..=64 => { IVA_C17_64.fetch_add(1, Relaxed); }
        _ => { IVA_C65P.fetch_add(1, Relaxed); }
    }
}

pub fn print_infer_value_atlas() {
    eprintln!(
        "INFER_VALUE_ATLAS misses={} repeats={} repeat_infer_calls={} max_infer_calls={} repeat_ns={} max_ns={} closed_results={} app={} lambda={} pi={} let={} proj={} c1={} c2_4={} c5_16={} c17_64={} c65p={}",
        IVA_MISSES.load(Relaxed),
        IVA_REPEATS.load(Relaxed),
        IVA_REPEAT_INFER_CALLS.load(Relaxed),
        IVA_MAX_INFER_CALLS.load(Relaxed),
        IVA_REPEAT_NS.load(Relaxed),
        IVA_MAX_NS.load(Relaxed),
        IVA_CLOSED_RESULTS.load(Relaxed),
        IVA_APP.load(Relaxed),
        IVA_LAMBDA.load(Relaxed),
        IVA_PI.load(Relaxed),
        IVA_LET.load(Relaxed),
        IVA_PROJ.load(Relaxed),
        IVA_C1.load(Relaxed),
        IVA_C2_4.load(Relaxed),
        IVA_C5_16.load(Relaxed),
        IVA_C17_64.load(Relaxed),
        IVA_C65P.load(Relaxed),
    );
}

"""
assert marker in s
s=s.replace(marker,stats+marker,1)

impl_marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n    fn uparam_scope(&self) -> CheckScope<'t> {\n"
helpers="""impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn cq_infer_rep(&self, v: V<'t>) -> V<'t> {
        if v.is_canonical() {
            v
        } else {
            let key = v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
        }
    }

    fn uparam_scope(&self) -> CheckScope<'t> {
"""
assert impl_marker in s
s=s.replace(impl_marker,helpers,1)

old="""    pub(crate) fn infer_value(
        &mut self,
        flag: InferFlag,
        depth: u32,
        env: E<'t>,
        ctx: C<'t>,
        e: ExprPtr<'t>,
    ) -> V<'t> {
        match self.ctx.read_expr(e) {
"""
new="""    pub(crate) fn infer_value(
        &mut self,
        flag: InferFlag,
        depth: u32,
        env: E<'t>,
        ctx: C<'t>,
        e: ExprPtr<'t>,
    ) -> V<'t> {
        IVA_INFER_CALLS.fetch_add(1, Relaxed);
        match self.ctx.read_expr(e) {
"""
assert old in s
s=s.replace(old,new,1)

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

        IVA_MISSES.fetch_add(1, Relaxed);

        let mode: u8 = if flag == InferOnly { 0 } else { 1 };
        let scope_key: u64 = if flag == InferOnly {
            0
        } else {
            match scope {
                CheckScope::Unchecked => 0,
                CheckScope::NoUparams => 1,
                CheckScope::Under(ls) => ls.get_hash().wrapping_add(2),
            }
        };

        let lsub_addr = te.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let (env_mask, env_reps): (u64, Vec<usize>) = match te {
            value::Env::Nil { .. } => (0, Vec::new()),
            value::Env::Framed { mask, slots, .. } => (
                *mask,
                slots.iter().map(|v| {
                    self.cq_infer_rep(*v) as *const Value<'t> as usize
                }).collect(),
            ),
            value::Env::Cons { .. } => (
                u64::MAX,
                vec![te as *const value::Env<'t> as usize],
            ),
        };

        let loose = e.num_loose_bvars();
        let mut ctx_reps: Vec<usize> = Vec::with_capacity(loose as usize);
        for i in 0..loose {
            let p = ctx.lookup(i).map_or(0, |v| {
                self.cq_infer_rep(v) as *const Value<'t> as usize
            });
            ctx_reps.push(p);
        }

        let shadow_key = (e, mode, scope_key, env_mask, lsub_addr, env_reps, ctx_reps);
        let shadow_repeat = !self.tc_cache.cq_infer_shadow.insert(shadow_key);
        let before_calls = if shadow_repeat { IVA_INFER_CALLS.load(Relaxed) } else { 0 };
        let started = if shadow_repeat { Some(Instant::now()) } else { None };

        let r = match self.ctx.read_expr(e) {
"""
assert old in s
s=s.replace(old,new,1)

old="""        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });
        r
"""
new="""        if shadow_repeat {
            IVA_REPEATS.fetch_add(1, Relaxed);
            let after_calls = IVA_INFER_CALLS.load(Relaxed);
            iva_record_calls(after_calls.saturating_sub(before_calls));
            if let Some(t0) = started {
                let ns = t0.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                IVA_REPEAT_NS.fetch_add(ns, Relaxed);
                IVA_MAX_NS.fetch_max(ns, Relaxed);
            }
            if r.is_closed() {
                IVA_CLOSED_RESULTS.fetch_add(1, Relaxed);
            }
            match self.ctx.read_expr(e) {
                App { .. } => { IVA_APP.fetch_add(1, Relaxed); }
                Lambda { .. } => { IVA_LAMBDA.fetch_add(1, Relaxed); }
                Pi { .. } => { IVA_PI.fetch_add(1, Relaxed); }
                Let { .. } => { IVA_LET.fetch_add(1, Relaxed); }
                Proj { .. } => { IVA_PROJ.fetch_add(1, Relaxed); }
                _ => {}
            }
        }

        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };
        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });
        r
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p=Path("a6/src/main.rs")
s=p.read_text()
old="""    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new="""    if std::env::var_os("SOKONANODA_INFER_VALUE_ATLAS").is_some() {
        sokonanoda::infer::print_infer_value_atlas();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
