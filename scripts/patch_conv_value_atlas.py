from pathlib import Path

# Diagnostic-only Consequence Value Atlas for conversion/unification.
#
# Existing conv_uf / negative caches remain authoritative.
# After they miss, derive a shadow identity from already-earned canonical
# representatives plus all explicit control state that can affect a bounded
# unify call: RIGID mode, depth, probe depth, and remaining probe budget.
#
# First occurrence stores the actual computed boolean result. Repeated shadow
# signatures are recomputed normally, timed/counted, and checked for
# contradiction. No shadow result is ever returned.

p=Path("a6/src/util.rs")
s=p.read_text()

field_marker="    pub(crate) conv_cache_neg_probe: FxHashSet<(usize, usize)>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_conv_shadow: "
    "FxHashMap<(usize, usize, u8, u32, u32, u32), bool>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)

init_marker="            conv_cache_neg_probe: small_fx_hash_set(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_conv_shadow: FxHashMap::default(),\n",1)

clear_marker="        self.conv_cache_neg_probe.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_conv_shadow.clear();\n",1)

session_marker="        shrink_set(&mut self.conv_cache_neg_probe);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_map(&mut self.cq_conv_shadow);\n",1)
p.write_text(s)

p=Path("a6/src/conv.rs")
s=p.read_text()

s=s.replace(
    "use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n",
    "use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nuse std::time::Instant;\n",
    1,
)

marker="fn rigid_head_eq<'a>(hx: RigidHead<'a>, hy: RigidHead<'a>) -> bool {\n"
stats="""static CVA_UNIFY_CALLS: AtomicU64 = AtomicU64::new(0);
static CVA_CACHE_MISSES: AtomicU64 = AtomicU64::new(0);
static CVA_REPEATS: AtomicU64 = AtomicU64::new(0);
static CVA_REPEAT_UNIFY_CALLS: AtomicU64 = AtomicU64::new(0);
static CVA_MAX_UNIFY_CALLS: AtomicU64 = AtomicU64::new(0);
static CVA_REPEAT_NS: AtomicU64 = AtomicU64::new(0);
static CVA_MAX_NS: AtomicU64 = AtomicU64::new(0);
static CVA_TRUE: AtomicU64 = AtomicU64::new(0);
static CVA_FALSE: AtomicU64 = AtomicU64::new(0);
static CVA_CONTRADICTIONS: AtomicU64 = AtomicU64::new(0);
static CVA_B1: AtomicU64 = AtomicU64::new(0);
static CVA_B2_4: AtomicU64 = AtomicU64::new(0);
static CVA_B5_16: AtomicU64 = AtomicU64::new(0);
static CVA_B17_64: AtomicU64 = AtomicU64::new(0);
static CVA_B65_256: AtomicU64 = AtomicU64::new(0);
static CVA_B257P: AtomicU64 = AtomicU64::new(0);

#[inline]
fn cva_record_cost(cost: u64) {
    CVA_REPEAT_UNIFY_CALLS.fetch_add(cost, Relaxed);
    CVA_MAX_UNIFY_CALLS.fetch_max(cost, Relaxed);
    match cost {
        0 | 1 => { CVA_B1.fetch_add(1, Relaxed); }
        2..=4 => { CVA_B2_4.fetch_add(1, Relaxed); }
        5..=16 => { CVA_B5_16.fetch_add(1, Relaxed); }
        17..=64 => { CVA_B17_64.fetch_add(1, Relaxed); }
        65..=256 => { CVA_B65_256.fetch_add(1, Relaxed); }
        _ => { CVA_B257P.fetch_add(1, Relaxed); }
    }
}

pub fn print_conv_value_atlas() {
    eprintln!(
        "CONV_VALUE_ATLAS cache_misses={} repeats={} repeat_unify_calls={} max_unify_calls={} repeat_ns={} max_ns={} true={} false={} contradictions={} b1={} b2_4={} b5_16={} b17_64={} b65_256={} b257p={}",
        CVA_CACHE_MISSES.load(Relaxed),
        CVA_REPEATS.load(Relaxed),
        CVA_REPEAT_UNIFY_CALLS.load(Relaxed),
        CVA_MAX_UNIFY_CALLS.load(Relaxed),
        CVA_REPEAT_NS.load(Relaxed),
        CVA_MAX_NS.load(Relaxed),
        CVA_TRUE.load(Relaxed),
        CVA_FALSE.load(Relaxed),
        CVA_CONTRADICTIONS.load(Relaxed),
        CVA_B1.load(Relaxed),
        CVA_B2_4.load(Relaxed),
        CVA_B5_16.load(Relaxed),
        CVA_B17_64.load(Relaxed),
        CVA_B65_256.load(Relaxed),
        CVA_B257P.load(Relaxed),
    );
}

"""
assert marker in s
s=s.replace(marker,stats+marker,1)

impl_marker="impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {\n    pub(crate) fn def_eq_core"
helpers="""impl<'x, 't, 'p> TypeChecker<'x, 't, 'p> {
    #[inline]
    fn cq_conv_rep(&self, v: V<'t>) -> V<'t> {
        if v.is_canonical() {
            v
        } else {
            let key = v as *const Value<'t> as usize;
            self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
        }
    }

    pub(crate) fn def_eq_core"""
assert impl_marker in s
s=s.replace(impl_marker,helpers,1)

old="""            let outer = std::mem::replace(&mut self.tc_cache.probe_exhausted, false);
            let result = self.unify_no_cache::<RIGID>(depth, x, y);
            let truncated = self.tc_cache.probe_exhausted;
            self.tc_cache.probe_exhausted = outer | truncated;
            if result {
"""
new="""            CVA_CACHE_MISSES.fetch_add(1, Relaxed);

            let rx = self.cq_conv_rep(x) as *const Value<'t> as usize;
            let ry = self.cq_conv_rep(y) as *const Value<'t> as usize;
            let (ra, rb) = if rx < ry { (rx, ry) } else { (ry, rx) };
            let mode: u8 = if RIGID { 1 } else { 0 };
            let shadow_key = (
                ra,
                rb,
                mode,
                depth,
                self.tc_cache.probe_depth,
                if self.tc_cache.probe_depth > 0 { self.tc_cache.probe_budget } else { 0 },
            );
            let expected = self.tc_cache.cq_conv_shadow.get(&shadow_key).copied();
            let before_calls = if expected.is_some() { CVA_UNIFY_CALLS.load(Relaxed) } else { 0 };
            let started = if expected.is_some() { Some(Instant::now()) } else { None };

            let outer = std::mem::replace(&mut self.tc_cache.probe_exhausted, false);
            let result = self.unify_no_cache::<RIGID>(depth, x, y);
            let truncated = self.tc_cache.probe_exhausted;
            self.tc_cache.probe_exhausted = outer | truncated;

            if let Some(first) = expected {
                CVA_REPEATS.fetch_add(1, Relaxed);
                let after_calls = CVA_UNIFY_CALLS.load(Relaxed);
                cva_record_cost(after_calls.saturating_sub(before_calls));
                if let Some(t0) = started {
                    let ns = t0.elapsed().as_nanos().min(u64::MAX as u128) as u64;
                    CVA_REPEAT_NS.fetch_add(ns, Relaxed);
                    CVA_MAX_NS.fetch_max(ns, Relaxed);
                }
                if result { CVA_TRUE.fetch_add(1, Relaxed); }
                else { CVA_FALSE.fetch_add(1, Relaxed); }
                if first != result {
                    CVA_CONTRADICTIONS.fetch_add(1, Relaxed);
                }
            } else {
                self.tc_cache.cq_conv_shadow.insert(shadow_key, result);
            }

            if result {
"""
assert old in s
s=s.replace(old,new,1)

old="""    fn unify_no_cache<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {
        if self.tc_cache.probe_depth > 0 {
"""
new="""    fn unify_no_cache<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {
        CVA_UNIFY_CALLS.fetch_add(1, Relaxed);
        if self.tc_cache.probe_depth > 0 {
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
new="""    if std::env::var_os("SOKONANODA_CONV_VALUE_ATLAS").is_some() {
        sokonanoda::conv::print_conv_value_atlas();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
