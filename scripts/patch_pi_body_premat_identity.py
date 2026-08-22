from pathlib import Path

conv = Path('kernel/src/conv.rs')
s = conv.read_text()

anchor = 'use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n'
insert = r'''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static PM_ENTER: AtomicU64 = AtomicU64::new(0);
static PM_BODY_SAME: AtomicU64 = AtomicU64::new(0);
static PM_ENV_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static PM_ENV_SEM_SAME: AtomicU64 = AtomicU64::new(0);
static PM_DOMAIN_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static PM_BODY_ENV_SEM_SAME: AtomicU64 = AtomicU64::new(0);
static PM_BODY_ENV_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static PM_POST_PTR_EQ: AtomicU64 = AtomicU64::new(0);
static PM_POST_PTR_EQ_GIVEN_BODY_SAME: AtomicU64 = AtomicU64::new(0);
static PM_POST_PTR_EQ_GIVEN_BODY_ENV_SEM: AtomicU64 = AtomicU64::new(0);
static PM_POST_PTR_EQ_GIVEN_BODY_ENV_PTR: AtomicU64 = AtomicU64::new(0);
static PM_POST_NONPTR_UNIFY_TRUE: AtomicU64 = AtomicU64::new(0);
static PM_POST_NONPTR_UNIFY_FALSE: AtomicU64 = AtomicU64::new(0);
static PM_BODY_SAME_POST_NONPTR_TRUE: AtomicU64 = AtomicU64::new(0);
static PM_BODY_DIFF_POST_NONPTR_TRUE: AtomicU64 = AtomicU64::new(0);

pub fn print_pi_body_premat_census() {
    if std::env::var_os("MG_PI_BODY_PREMAT").is_none() { return; }
    macro_rules! p { ($n:literal,$x:expr) => { eprintln!("MG_PI_PREMAT {}={}", $n, $x.load(Relaxed)); }; }
    p!("enter", PM_ENTER);
    p!("body_same", PM_BODY_SAME);
    p!("env_ptr_same", PM_ENV_PTR_SAME);
    p!("env_sem_same", PM_ENV_SEM_SAME);
    p!("domain_ptr_same", PM_DOMAIN_PTR_SAME);
    p!("body_env_sem_same", PM_BODY_ENV_SEM_SAME);
    p!("body_env_ptr_same", PM_BODY_ENV_PTR_SAME);
    p!("post_ptr_eq", PM_POST_PTR_EQ);
    p!("post_ptr_eq_given_body_same", PM_POST_PTR_EQ_GIVEN_BODY_SAME);
    p!("post_ptr_eq_given_body_env_sem", PM_POST_PTR_EQ_GIVEN_BODY_ENV_SEM);
    p!("post_ptr_eq_given_body_env_ptr", PM_POST_PTR_EQ_GIVEN_BODY_ENV_PTR);
    p!("post_nonptr_unify_true", PM_POST_NONPTR_UNIFY_TRUE);
    p!("post_nonptr_unify_false", PM_POST_NONPTR_UNIFY_FALSE);
    p!("body_same_post_nonptr_true", PM_BODY_SAME_POST_NONPTR_TRUE);
    p!("body_diff_post_nonptr_true", PM_BODY_DIFF_POST_NONPTR_TRUE);
}
'''
if anchor not in s: raise SystemExit('import anchor missing')
s = s.replace(anchor, anchor + insert, 1)

old = '''                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                self.unify::<RIGID>(depth + 1, vx, vy)'''
new = '''                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                PM_ENTER.fetch_add(1, Relaxed);\n                let body_same = bx.body == by.body;\n                let env_ptr_same = std::ptr::eq(bx.env, by.env);\n                let env_sem_same = Self::envs_ptr_equal(bx.env, by.env);\n                let domain_ptr_same = std::ptr::eq(*dx, *dy);\n                if body_same { PM_BODY_SAME.fetch_add(1, Relaxed); }\n                if env_ptr_same { PM_ENV_PTR_SAME.fetch_add(1, Relaxed); }\n                if env_sem_same { PM_ENV_SEM_SAME.fetch_add(1, Relaxed); }\n                if domain_ptr_same { PM_DOMAIN_PTR_SAME.fetch_add(1, Relaxed); }\n                if body_same && env_sem_same { PM_BODY_ENV_SEM_SAME.fetch_add(1, Relaxed); }\n                if body_same && env_ptr_same { PM_BODY_ENV_PTR_SAME.fetch_add(1, Relaxed); }\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                let post_ptr = std::ptr::eq(vx, vy);\n                if post_ptr {\n                    PM_POST_PTR_EQ.fetch_add(1, Relaxed);\n                    if body_same { PM_POST_PTR_EQ_GIVEN_BODY_SAME.fetch_add(1, Relaxed); }\n                    if body_same && env_sem_same { PM_POST_PTR_EQ_GIVEN_BODY_ENV_SEM.fetch_add(1, Relaxed); }\n                    if body_same && env_ptr_same { PM_POST_PTR_EQ_GIVEN_BODY_ENV_PTR.fetch_add(1, Relaxed); }\n                }\n                let r = self.unify::<RIGID>(depth + 1, vx, vy);\n                if !post_ptr {\n                    if r {\n                        PM_POST_NONPTR_UNIFY_TRUE.fetch_add(1, Relaxed);\n                        if body_same { PM_BODY_SAME_POST_NONPTR_TRUE.fetch_add(1, Relaxed); }\n                        else { PM_BODY_DIFF_POST_NONPTR_TRUE.fetch_add(1, Relaxed); }\n                    } else { PM_POST_NONPTR_UNIFY_FALSE.fetch_add(1, Relaxed); }\n                }\n                r'''
if old not in s: raise SystemExit('Pi body anchor missing')
s = s.replace(old, new, 1)
conv.write_text(s)

main = Path('kernel/src/main.rs')
m = main.read_text()
oldm = '''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
newm = '''    sokonanoda::conv::print_pi_body_premat_census();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if oldm not in m: raise SystemExit('main anchor missing')
m = m.replace(oldm, newm, 1)
main.write_text(m)
print('patched Pi-body pre-materialization identity census')
