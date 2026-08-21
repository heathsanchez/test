from pathlib import Path

conv = Path('kernel/src/conv.rs')
s = conv.read_text()

anchor = 'use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n'
insert = r'''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static PF_UNIFY_ENTER: AtomicU64 = AtomicU64::new(0);
static PF_PTR_PRE: AtomicU64 = AtomicU64::new(0);
static PF_PTR_AFTER_LEFT: AtomicU64 = AtomicU64::new(0);
static PF_PTR_AFTER_BOTH: AtomicU64 = AtomicU64::new(0);
static PF_FORCE_LEFT_CHANGED: AtomicU64 = AtomicU64::new(0);
static PF_FORCE_RIGHT_CHANGED: AtomicU64 = AtomicU64::new(0);

static PI_ENTER: AtomicU64 = AtomicU64::new(0);
static PI_BODY_SAME: AtomicU64 = AtomicU64::new(0);
static PI_DOMAIN_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static PI_ENV_SAME_WHEN_ELIGIBLE: AtomicU64 = AtomicU64::new(0);
static PI_FAST_ALL: AtomicU64 = AtomicU64::new(0);
static PI_DOMAIN_PTR_NONFAST: AtomicU64 = AtomicU64::new(0);
static PI_DOMAIN_UNIFY_TRUE: AtomicU64 = AtomicU64::new(0);
static PI_DOMAIN_UNIFY_FALSE: AtomicU64 = AtomicU64::new(0);
static PI_BODY_UNIFY_TRUE: AtomicU64 = AtomicU64::new(0);
static PI_BODY_UNIFY_FALSE: AtomicU64 = AtomicU64::new(0);
static PI_CLOSURE_APPLY_PAIR: AtomicU64 = AtomicU64::new(0);

pub fn print_preforce_pi_sniff() {
    if std::env::var_os("MG_PREFORCE_PI_SNIFF").is_none() { return; }
    macro_rules! p { ($n:literal, $x:expr) => { eprintln!("MG_PREFORCE_PI {}={}", $n, $x.load(Relaxed)); }; }
    p!("unify_enter", PF_UNIFY_ENTER);
    p!("ptr_pre", PF_PTR_PRE);
    p!("ptr_after_left", PF_PTR_AFTER_LEFT);
    p!("ptr_after_both", PF_PTR_AFTER_BOTH);
    p!("force_left_changed", PF_FORCE_LEFT_CHANGED);
    p!("force_right_changed", PF_FORCE_RIGHT_CHANGED);
    p!("pi_enter", PI_ENTER);
    p!("pi_body_same", PI_BODY_SAME);
    p!("pi_domain_ptr_same", PI_DOMAIN_PTR_SAME);
    p!("pi_env_same_when_eligible", PI_ENV_SAME_WHEN_ELIGIBLE);
    p!("pi_fast_all", PI_FAST_ALL);
    p!("pi_domain_ptr_nonfast", PI_DOMAIN_PTR_NONFAST);
    p!("pi_domain_unify_true", PI_DOMAIN_UNIFY_TRUE);
    p!("pi_domain_unify_false", PI_DOMAIN_UNIFY_FALSE);
    p!("pi_body_unify_true", PI_BODY_UNIFY_TRUE);
    p!("pi_body_unify_false", PI_BODY_UNIFY_FALSE);
    p!("pi_closure_apply_pair", PI_CLOSURE_APPLY_PAIR);
}
'''
if anchor not in s:
    raise SystemExit('conv import anchor missing')
s = s.replace(anchor, anchor + insert, 1)

old_unify = '''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        let x = self.force_thunk(depth, x);\n        let y = self.force_thunk(depth, y);\n        if std::ptr::eq(x, y) {\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
new_unify = '''    #[inline]\n    fn unify<const RIGID: bool>(&mut self, depth: u32, x: V<'t>, y: V<'t>) -> bool {\n        PF_UNIFY_ENTER.fetch_add(1, Relaxed);\n        if std::ptr::eq(x, y) {\n            PF_PTR_PRE.fetch_add(1, Relaxed);\n        }\n        let x0 = x;\n        let y0 = y;\n        let x = self.force_thunk(depth, x);\n        if !std::ptr::eq(x0, x) { PF_FORCE_LEFT_CHANGED.fetch_add(1, Relaxed); }\n        if !std::ptr::eq(x0, y0) && std::ptr::eq(x, y0) {\n            PF_PTR_AFTER_LEFT.fetch_add(1, Relaxed);\n        }\n        let y = self.force_thunk(depth, y0);\n        if !std::ptr::eq(y0, y) { PF_FORCE_RIGHT_CHANGED.fetch_add(1, Relaxed); }\n        if std::ptr::eq(x, y) {\n            if !std::ptr::eq(x0, y0) && !std::ptr::eq(x, y0) {\n                PF_PTR_AFTER_BOTH.fetch_add(1, Relaxed);\n            }\n            return true;\n        }\n        self.unify_general::<RIGID>(depth, x, y)\n    }'''
if old_unify not in s:
    raise SystemExit('unify anchor missing')
s = s.replace(old_unify, new_unify, 1)

old_pi = '''            (Value::Pi { domain: dx, body: bx, .. }, Value::Pi { domain: dy, body: by, .. }) => {\n                if bx.body == by.body\n                    && std::ptr::eq(*dx, *dy)\n                    && Self::envs_ptr_equal(bx.env, by.env)\n                {\n                    return true;\n                }\n                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                self.unify::<RIGID>(depth + 1, vx, vy)\n            }'''
new_pi = '''            (Value::Pi { domain: dx, body: bx, .. }, Value::Pi { domain: dy, body: by, .. }) => {\n                PI_ENTER.fetch_add(1, Relaxed);\n                let body_same = bx.body == by.body;\n                let domain_ptr_same = std::ptr::eq(*dx, *dy);\n                if body_same { PI_BODY_SAME.fetch_add(1, Relaxed); }\n                if domain_ptr_same { PI_DOMAIN_PTR_SAME.fetch_add(1, Relaxed); }\n                let env_same = if body_same && domain_ptr_same {\n                    let z = Self::envs_ptr_equal(bx.env, by.env);\n                    if z { PI_ENV_SAME_WHEN_ELIGIBLE.fetch_add(1, Relaxed); }\n                    z\n                } else { false };\n                if body_same && domain_ptr_same && env_same {\n                    PI_FAST_ALL.fetch_add(1, Relaxed);\n                    return true;\n                }\n                if domain_ptr_same { PI_DOMAIN_PTR_NONFAST.fetch_add(1, Relaxed); }\n                if !self.unify::<RIGID>(depth, dx, dy) {\n                    PI_DOMAIN_UNIFY_FALSE.fetch_add(1, Relaxed);\n                    return false;\n                }\n                PI_DOMAIN_UNIFY_TRUE.fetch_add(1, Relaxed);\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                PI_CLOSURE_APPLY_PAIR.fetch_add(1, Relaxed);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                let r = self.unify::<RIGID>(depth + 1, vx, vy);\n                if r { PI_BODY_UNIFY_TRUE.fetch_add(1, Relaxed); } else { PI_BODY_UNIFY_FALSE.fetch_add(1, Relaxed); }\n                r\n            }'''
if old_pi not in s:
    raise SystemExit('Pi branch anchor missing')
s = s.replace(old_pi, new_pi, 1)
conv.write_text(s)

main = Path('kernel/src/main.rs')
m = main.read_text()
oldm = '''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
newm = '''    sokonanoda::conv::print_preforce_pi_sniff();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if oldm not in m:
    raise SystemExit('main anchor missing')
m = m.replace(oldm, newm, 1)
main.write_text(m)
print('patched pre-force/Pi-Pi sniff instrumentation')
