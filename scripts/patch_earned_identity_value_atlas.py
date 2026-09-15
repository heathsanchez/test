from pathlib import Path

# Diagnostic-only atlas for reuse opportunities whose semantic identity has
# ALREADY been earned by the checker.
#
# No canonicalization is triggered here. A value participates only when:
#   - it is already canonical, or
#   - canon_cache already maps its raw pointer to a canonical representative.
#
# Existing production caches remain authoritative. Shadow maps merely detect
# raw-cache misses that collapse to an already-known canonical representative
# and measure the work subsequently recomputed.

p=Path("a6/src/util.rs")
s=p.read_text()

# Shadow sets for already-earned identities.
field_marker="    pub(crate) quote_cache: FxHashMap<(usize, u32), ExprPtr<'t>>,\n"
field_insert=field_marker+"""    pub(crate) earned_quote_shadow: FxHashSet<(usize, u32)>,
    pub(crate) earned_global_shadow: FxHashSet<(usize, u32)>,
    pub(crate) earned_struct_eta_shadow: FxHashSet<(usize, NamePtr<'t>)>,
"""
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            quote_cache: session_fx_hash_map(),\n"
init_insert=init_marker+"""            earned_quote_shadow: FxHashSet::default(),
            earned_global_shadow: FxHashSet::default(),
            earned_struct_eta_shadow: FxHashSet::default(),
"""
assert init_marker in s
s=s.replace(init_marker,init_insert,1)

clear_marker="        self.quote_cache.clear();\n"
clear_insert=clear_marker+"""        self.earned_quote_shadow.clear();
        self.earned_global_shadow.clear();
        self.earned_struct_eta_shadow.clear();
"""
assert clear_marker in s
s=s.replace(clear_marker,clear_insert,1)

session_marker="        shrink_map(&mut self.quote_cache);\n"
session_insert=session_marker+"""        shrink_set(&mut self.earned_quote_shadow);
        shrink_set(&mut self.earned_global_shadow);
        shrink_set(&mut self.earned_struct_eta_shadow);
"""
assert session_marker in s
s=s.replace(session_marker,session_insert,1)
p.write_text(s)

# ---- quote atlas ----
p=Path("a6/src/quote.rs")
s=p.read_text()
s=s.replace(
    "use crate::value::{ElimView, RigidHead, Spine, Value, E, S, V};\n",
    "use crate::value::{ElimView, RigidHead, Spine, Value, E, S, V};\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nuse std::time::Instant;\n",
    1,
)

marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n"
stats="""static EIA_QUOTE_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_MISSES: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_EARNED: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_REPEATS: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_REPEAT_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_MAX_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_REPEAT_NS: AtomicU64 = AtomicU64::new(0);
static EIA_QUOTE_MAX_NS: AtomicU64 = AtomicU64::new(0);

impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn earned_rep_for_quote(&self, v: V<'t>) -> Option<V<'t>> {
        if v.is_canonical() {
            Some(v)
        } else {
            let raw = v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&raw).copied()
        }
    }

"""
assert marker in s
s=s.replace(marker,stats,1)

old="""    pub(crate) fn quote(&mut self, depth: u32, v: V<'t>) -> ExprPtr<'t> {
        let v = self.force_thunk(depth, v);
        let key = (v as *const Value<'t> as usize, depth);
        if let Some(q) = self.tc_cache.quote_cache.get(&key).copied() {
            return q;
        }
        let r = match v {
"""
new="""    pub(crate) fn quote(&mut self, depth: u32, v: V<'t>) -> ExprPtr<'t> {
        EIA_QUOTE_CALLS.fetch_add(1, Relaxed);
        let v = self.force_thunk(depth, v);
        let key = (v as *const Value<'t> as usize, depth);
        if let Some(q) = self.tc_cache.quote_cache.get(&key).copied() {
            return q;
        }
        EIA_QUOTE_MISSES.fetch_add(1, Relaxed);

        let earned_key = self.earned_rep_for_quote(v).map(|r| {
            EIA_QUOTE_EARNED.fetch_add(1, Relaxed);
            (r as *const Value<'t> as usize, depth)
        });
        let repeat = earned_key.map_or(false, |k| !self.tc_cache.earned_quote_shadow.insert(k));
        let before_calls = if repeat { EIA_QUOTE_CALLS.load(Relaxed) } else { 0 };
        let started = if repeat { Some(Instant::now()) } else { None };

        let r = match v {
"""
assert old in s
s=s.replace(old,new,1)

old="""        self.tc_cache.quote_cache.insert(key, r);
        r
    }
"""
new="""        if repeat {
            EIA_QUOTE_REPEATS.fetch_add(1, Relaxed);
            let calls=EIA_QUOTE_CALLS.load(Relaxed).saturating_sub(before_calls);
            EIA_QUOTE_REPEAT_CALLS.fetch_add(calls, Relaxed);
            EIA_QUOTE_MAX_CALLS.fetch_max(calls, Relaxed);
            if let Some(t0)=started {
                let ns=t0.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                EIA_QUOTE_REPEAT_NS.fetch_add(ns, Relaxed);
                EIA_QUOTE_MAX_NS.fetch_max(ns, Relaxed);
            }
        }
        self.tc_cache.quote_cache.insert(key, r);
        r
    }
"""
assert old in s
s=s.replace(old,new,1)
s += """

pub fn print_earned_quote_atlas() {
    eprintln!(
        "EARNED_QUOTE_ATLAS misses={} earned_identity_misses={} repeats={} repeat_calls={} max_calls={} repeat_ns={} max_ns={}",
        EIA_QUOTE_MISSES.load(Relaxed),
        EIA_QUOTE_EARNED.load(Relaxed),
        EIA_QUOTE_REPEATS.load(Relaxed),
        EIA_QUOTE_REPEAT_CALLS.load(Relaxed),
        EIA_QUOTE_MAX_CALLS.load(Relaxed),
        EIA_QUOTE_REPEAT_NS.load(Relaxed),
        EIA_QUOTE_MAX_NS.load(Relaxed),
    );
}
"""
p.write_text(s)

# ---- global key + struct eta atlases ----
p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nuse std::time::Instant;\n",
    1,
)

# Place statics near constants.
marker="const WHNF_ADMIT_THRESHOLD: u8 = 2;\n"
stats=marker+"""
static EIA_GLOBAL_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_MISSES: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_EARNED: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_REPEATS: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_REPEAT_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_MAX_CALLS: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_REPEAT_NS: AtomicU64 = AtomicU64::new(0);
static EIA_GLOBAL_MAX_NS: AtomicU64 = AtomicU64::new(0);

static EIA_STRUCT_MISSES: AtomicU64 = AtomicU64::new(0);
static EIA_STRUCT_EARNED: AtomicU64 = AtomicU64::new(0);
static EIA_STRUCT_REPEATS: AtomicU64 = AtomicU64::new(0);
static EIA_STRUCT_REPEAT_NS: AtomicU64 = AtomicU64::new(0);
static EIA_STRUCT_MAX_NS: AtomicU64 = AtomicU64::new(0);
"""
assert marker in s
s=s.replace(marker,stats,1)

# helper at start of impl
impl_marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n"
helper="""impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn earned_rep_existing(&self, v: V<'t>) -> Option<V<'t>> {
        if v.is_canonical() {
            Some(v)
        } else {
            let raw=v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&raw).copied()
        }
    }

"""
assert impl_marker in s
s=s.replace(impl_marker,helper,1)

old="""    fn global_key(&mut self, v: V<'t>, depth: u32) -> Result<(u128, bool), u8> {
        let addr = v as *const Value<'t> as usize;
        if let Some(&k) = self.tc_cache.global_value_cache.get(&(addr, depth)) {
            return k;
        }
        let r = self.global_key_uncached(v, depth);
        self.tc_cache.global_value_cache.insert((addr, depth), r);
        r
    }
"""
new="""    fn global_key(&mut self, v: V<'t>, depth: u32) -> Result<(u128, bool), u8> {
        EIA_GLOBAL_CALLS.fetch_add(1, Relaxed);
        let addr = v as *const Value<'t> as usize;
        if let Some(&k) = self.tc_cache.global_value_cache.get(&(addr, depth)) {
            return k;
        }
        EIA_GLOBAL_MISSES.fetch_add(1, Relaxed);
        let earned_key=self.earned_rep_existing(v).map(|r| {
            EIA_GLOBAL_EARNED.fetch_add(1, Relaxed);
            (r as *const Value<'t> as usize, depth)
        });
        let repeat=earned_key.map_or(false, |k| !self.tc_cache.earned_global_shadow.insert(k));
        let before_calls=if repeat { EIA_GLOBAL_CALLS.load(Relaxed) } else { 0 };
        let started=if repeat { Some(Instant::now()) } else { None };

        let r = self.global_key_uncached(v, depth);

        if repeat {
            EIA_GLOBAL_REPEATS.fetch_add(1, Relaxed);
            let calls=EIA_GLOBAL_CALLS.load(Relaxed).saturating_sub(before_calls);
            EIA_GLOBAL_REPEAT_CALLS.fetch_add(calls, Relaxed);
            EIA_GLOBAL_MAX_CALLS.fetch_max(calls, Relaxed);
            if let Some(t0)=started {
                let ns=t0.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                EIA_GLOBAL_REPEAT_NS.fetch_add(ns, Relaxed);
                EIA_GLOBAL_MAX_NS.fetch_max(ns, Relaxed);
            }
        }
        self.tc_cache.global_value_cache.insert((addr, depth), r);
        r
    }
"""
assert old in s
s=s.replace(old,new,1)

old="""        let key = (major as *const Value<'t> as usize, rec_induct);
        if let Some(cached) = self.tc_cache.struct_eta_cache.get(&key) {
            return *cached;
        }
        let result = self.try_struct_eta_reduce_uncached(depth, major, rec, rec_induct);
        self.tc_cache.struct_eta_cache.insert(key, result);
        result
"""
new="""        let key = (major as *const Value<'t> as usize, rec_induct);
        if let Some(cached) = self.tc_cache.struct_eta_cache.get(&key) {
            return *cached;
        }
        EIA_STRUCT_MISSES.fetch_add(1, Relaxed);
        let earned_key=self.earned_rep_existing(major).map(|r| {
            EIA_STRUCT_EARNED.fetch_add(1, Relaxed);
            (r as *const Value<'t> as usize, rec_induct)
        });
        let repeat=earned_key.map_or(false, |k| !self.tc_cache.earned_struct_eta_shadow.insert(k));
        let started=if repeat { Some(Instant::now()) } else { None };

        let result = self.try_struct_eta_reduce_uncached(depth, major, rec, rec_induct);

        if repeat {
            EIA_STRUCT_REPEATS.fetch_add(1, Relaxed);
            if let Some(t0)=started {
                let ns=t0.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                EIA_STRUCT_REPEAT_NS.fetch_add(ns, Relaxed);
                EIA_STRUCT_MAX_NS.fetch_max(ns, Relaxed);
            }
        }
        self.tc_cache.struct_eta_cache.insert(key, result);
        result
"""
assert old in s
s=s.replace(old,new,1)

s += """

pub fn print_earned_eval_atlas() {
    eprintln!(
        "EARNED_GLOBAL_ATLAS misses={} earned_identity_misses={} repeats={} repeat_calls={} max_calls={} repeat_ns={} max_ns={}",
        EIA_GLOBAL_MISSES.load(Relaxed),
        EIA_GLOBAL_EARNED.load(Relaxed),
        EIA_GLOBAL_REPEATS.load(Relaxed),
        EIA_GLOBAL_REPEAT_CALLS.load(Relaxed),
        EIA_GLOBAL_MAX_CALLS.load(Relaxed),
        EIA_GLOBAL_REPEAT_NS.load(Relaxed),
        EIA_GLOBAL_MAX_NS.load(Relaxed),
    );
    eprintln!(
        "EARNED_STRUCT_ETA_ATLAS misses={} earned_identity_misses={} repeats={} repeat_ns={} max_ns={}",
        EIA_STRUCT_MISSES.load(Relaxed),
        EIA_STRUCT_EARNED.load(Relaxed),
        EIA_STRUCT_REPEATS.load(Relaxed),
        EIA_STRUCT_REPEAT_NS.load(Relaxed),
        EIA_STRUCT_MAX_NS.load(Relaxed),
    );
}
"""
p.write_text(s)

# ---- main printer ----
p=Path("a6/src/main.rs")
s=p.read_text()
old="""    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new="""    if std::env::var_os("SOKONANODA_EARNED_IDENTITY_ATLAS").is_some() {
        sokonanoda::quote::print_earned_quote_atlas();
        sokonanoda::eval::print_earned_eval_atlas();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
# TypeChecker associated fn inaccessible this way; use module free wrappers instead later.
# Adjust eval printer to free fn, quote printer to free fn for easy calls.
# Modify generated source snippets accordingly before writing main.
if old not in s:
    raise RuntimeError("main marker missing")
p.write_text(s.replace(old,new,1))
