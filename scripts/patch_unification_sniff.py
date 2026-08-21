from pathlib import Path

conv = Path('kernel/src/conv.rs')
s = conv.read_text()

anchor = 'use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n'
insert = r'''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};
use std::sync::LazyLock;

static SNIFF_UNIFY_ENTER: AtomicU64 = AtomicU64::new(0);
static SNIFF_PTR_EQ: AtomicU64 = AtomicU64::new(0);
static SNIFF_FORCE_LEFT_CHANGED: AtomicU64 = AtomicU64::new(0);
static SNIFF_FORCE_RIGHT_CHANGED: AtomicU64 = AtomicU64::new(0);
static SNIFF_CACHEABLE: AtomicU64 = AtomicU64::new(0);
static SNIFF_NONCACHEABLE: AtomicU64 = AtomicU64::new(0);
static SNIFF_UF_HIT: AtomicU64 = AtomicU64::new(0);
static SNIFF_NEG_HIT: AtomicU64 = AtomicU64::new(0);
static SNIFF_NEG_PROBE_HIT: AtomicU64 = AtomicU64::new(0);
static SNIFF_NO_CACHE_ENTER: AtomicU64 = AtomicU64::new(0);
static SNIFF_NAT_DECIDED: AtomicU64 = AtomicU64::new(0);
static SNIFF_NAT_TRUE: AtomicU64 = AtomicU64::new(0);
static SNIFF_DIRECT_TRUE: AtomicU64 = AtomicU64::new(0);
static SNIFF_COLD_ENTER: AtomicU64 = AtomicU64::new(0);
static SNIFF_COLD_TRUE: AtomicU64 = AtomicU64::new(0);
static SNIFF_COLD_FALSE: AtomicU64 = AtomicU64::new(0);
static SNIFF_PAIR: LazyLock<[AtomicU64; 64]> = LazyLock::new(|| std::array::from_fn(|_| AtomicU64::new(0)));

#[inline]
fn sniff_kind(v: V<'_>) -> usize {
    match v {
        Value::Rigid { .. } => 0,
        Value::Unfold { .. } => 1,
        Value::Lam { .. } => 2,
        Value::Pi { .. } => 3,
        Value::Sort { .. } => 4,
        Value::NatLit { .. } => 5,
        Value::StrLit { .. } => 6,
        Value::Thunk { .. } => 7,
    }
}

pub fn print_unification_sniff() {
    if std::env::var_os("MG_UNIFY_SNIFF").is_none() { return; }
    macro_rules! p { ($n:literal, $x:expr) => { eprintln!("MG_UNIFY_SNIFF {}={}", $n, $x.load(Relaxed)); }; }
    p!("unify_enter", SNIFF_UNIFY_ENTER);
    p!("ptr_eq", SNIFF_PTR_EQ);
    p!("force_left_changed", SNIFF_FORCE_LEFT_CHANGED);
    p!("force_right_changed", SNIFF_FORCE_RIGHT_CHANGED);
    p!("cacheable", SNIFF_CACHEABLE);
    p!("noncacheable", SNIFF_NONCACHEABLE);
    p!("uf_hit", SNIFF_UF_HIT);
    p!("neg_hit", SNIFF_NEG_HIT);
    p!("neg_probe_hit", SNIFF_NEG_PROBE_HIT);
    p!("no_cache_enter", SNIFF_NO_CACHE_ENTER);
    p!("nat_decided", SNIFF_NAT_DECIDED);
    p!("nat_true", SNIFF_NAT_TRUE);
    p!("direct_true", SNIFF_DIRECT_TRUE);
    p!("cold_enter", SNIFF_COLD_ENTER);
    p!("cold_true", SNIFF_COLD_TRUE);
    p!("cold_false", SNIFF_COLD_FALSE);
    for i in 0..8 {
        for j in 0..8 {
            let n = SNIFF_PAIR[i*8+j].load(Relaxed);
            if n != 0 { eprintln!("MG_UNIFY_PAIR {} {} {}", i, j, n); }
        }
    }
}
'''
if anchor not in s:
    raise SystemExit('conv import anchor missing')
s = s.replace(anchor, anchor + insert, 1)

old = '''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        let x = self.force_thunk(depth, x);\n        let y = self.force_thunk(depth, y);\n        if std::ptr::eq(x, y) {\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
new = '''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        SNIFF_UNIFY_ENTER.fetch_add(1, Relaxed);\n        let x0 = x;\n        let y0 = y;\n        let x = self.force_thunk(depth, x);\n        let y = self.force_thunk(depth, y);\n        if !std::ptr::eq(x0, x) { SNIFF_FORCE_LEFT_CHANGED.fetch_add(1, Relaxed); }\n        if !std::ptr::eq(y0, y) { SNIFF_FORCE_RIGHT_CHANGED.fetch_add(1, Relaxed); }\n        if std::ptr::eq(x, y) {\n            SNIFF_PTR_EQ.fetch_add(1, Relaxed);\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
if old not in s:
    raise SystemExit('unify anchor missing')
s = s.replace(old, new, 1)

s = s.replace('''        if cacheable {\n            let xa = x as *const Value<'t> as usize;''', '''        if cacheable {\n            SNIFF_CACHEABLE.fetch_add(1, Relaxed);\n            let xa = x as *const Value<'t> as usize;''', 1)
s = s.replace('''            if self.tc_cache.conv_uf.equiv(xa, ya) {\n                return true;\n            }''', '''            if self.tc_cache.conv_uf.equiv(xa, ya) {\n                SNIFF_UF_HIT.fetch_add(1, Relaxed);\n                return true;\n            }''', 1)
s = s.replace('''                if self.tc_cache.conv_cache_neg.contains(&cache_key) {\n                    return false;\n                }''', '''                if self.tc_cache.conv_cache_neg.contains(&cache_key) {\n                    SNIFF_NEG_HIT.fetch_add(1, Relaxed);\n                    return false;\n                }''', 1)
s = s.replace('''                if self.tc_cache.probe_depth > 0 && self.tc_cache.conv_cache_neg_probe.contains(&cache_key) {\n                    self.tc_cache.probe_exhausted = true;\n                    return false;\n                }''', '''                if self.tc_cache.probe_depth > 0 && self.tc_cache.conv_cache_neg_probe.contains(&cache_key) {\n                    SNIFF_NEG_PROBE_HIT.fetch_add(1, Relaxed);\n                    self.tc_cache.probe_exhausted = true;\n                    return false;\n                }''', 1)
s = s.replace('''        } else {\n            self.unify_no_cache::<RIGID>(depth, x, y)\n        }\n    }\n\n    const PROBE_CAP''', '''        } else {\n            SNIFF_NONCACHEABLE.fetch_add(1, Relaxed);\n            self.unify_no_cache::<RIGID>(depth, x, y)\n        }\n    }\n\n    const PROBE_CAP''', 1)

old2 = '''    fn unify_no_cache<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        if self.tc_cache.probe_depth > 0 {'''
new2 = '''    #[inline(never)]\n    fn sniff_nat_route<const RIGID: bool>(&mut self, depth: u32, t: V<'t>, t2: V<'t>) -> Option<bool> {\n        self.conv_nat::<RIGID>(depth, t, t2)\n    }\n\n    #[inline(never)]\n    fn sniff_direct_route<const RIGID: bool>(&mut self, depth: u32, t: V<'t>, t2: V<'t>) -> bool {\n        self.unify_direct::<RIGID>(depth, t, t2)\n    }\n\n    #[inline(never)]\n    fn sniff_cold_route<const RIGID: bool>(&mut self, depth: u32, t: V<'t>, t2: V<'t>) -> bool {\n        self.unify_cold::<RIGID>(depth, t, t2)\n    }\n\n    fn unify_no_cache<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        SNIFF_NO_CACHE_ENTER.fetch_add(1, Relaxed);\n        if self.tc_cache.probe_depth > 0 {'''
if old2 not in s:
    raise SystemExit('unify_no_cache anchor missing')
s = s.replace(old2, new2, 1)

old3 = '''        let (t, t2) = (self.force_thunk(depth, x), self.force_thunk(depth, y));\n        if let Some(r) = self.conv_nat::<RIGID>(depth, t, t2) {\n            return r;\n        }\n        if self.unify_direct::<RIGID>(depth, t, t2) {\n            return true;\n        }\n        self.unify_cold::<RIGID>(depth, t, t2)\n    }'''
new3 = '''        let (t, t2) = (self.force_thunk(depth, x), self.force_thunk(depth, y));\n        let ki = sniff_kind(t);\n        let kj = sniff_kind(t2);\n        SNIFF_PAIR[ki * 8 + kj].fetch_add(1, Relaxed);\n        if let Some(r) = self.sniff_nat_route::<RIGID>(depth, t, t2) {\n            SNIFF_NAT_DECIDED.fetch_add(1, Relaxed);\n            if r { SNIFF_NAT_TRUE.fetch_add(1, Relaxed); }\n            return r;\n        }\n        if self.sniff_direct_route::<RIGID>(depth, t, t2) {\n            SNIFF_DIRECT_TRUE.fetch_add(1, Relaxed);\n            return true;\n        }\n        SNIFF_COLD_ENTER.fetch_add(1, Relaxed);\n        let r = self.sniff_cold_route::<RIGID>(depth, t, t2);\n        if r { SNIFF_COLD_TRUE.fetch_add(1, Relaxed); } else { SNIFF_COLD_FALSE.fetch_add(1, Relaxed); }\n        r\n    }'''
if old3 not in s:
    raise SystemExit('route anchor missing')
s = s.replace(old3, new3, 1)
conv.write_text(s)

main = Path('kernel/src/main.rs')
m = main.read_text()
oldm = '''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
newm = '''    // Emit semantics-inert diagnostic counters only when explicitly requested.\n    sokonanoda::conv::print_unification_sniff();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if oldm not in m:
    raise SystemExit('main anchor missing')
m = m.replace(oldm, newm, 1)
main.write_text(m)
print('patched unification sniff instrumentation')
