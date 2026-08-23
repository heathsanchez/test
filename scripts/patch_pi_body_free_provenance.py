from pathlib import Path

conv = Path('kernel/src/conv.rs')
s = conv.read_text()
anchor = 'use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n'
insert = r'''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static FP_ENTER: AtomicU64 = AtomicU64::new(0);
static FP_BODY_SAME: AtomicU64 = AtomicU64::new(0);
static FP_ENV_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static FP_ENV_HASH_SAME: AtomicU64 = AtomicU64::new(0);
static FP_ENV_LEN_SAME: AtomicU64 = AtomicU64::new(0);
static FP_LSUB_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static FP_CTX_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static FP_DOMAIN_PTR_SAME: AtomicU64 = AtomicU64::new(0);
static FP_BODY_HASH: AtomicU64 = AtomicU64::new(0);
static FP_BODY_HASH_LEN: AtomicU64 = AtomicU64::new(0);
static FP_BODY_HASH_LEN_LSUB: AtomicU64 = AtomicU64::new(0);
static FP_BODY_HASH_LEN_LSUB_CTX: AtomicU64 = AtomicU64::new(0);
static FP_POST_PTR: AtomicU64 = AtomicU64::new(0);
static FP_POST_PTR_BODY_HASH: AtomicU64 = AtomicU64::new(0);
static FP_POST_PTR_BODY_HASH_LEN: AtomicU64 = AtomicU64::new(0);
static FP_POST_PTR_BODY_HASH_LEN_LSUB: AtomicU64 = AtomicU64::new(0);
static FP_POST_PTR_BODY_HASH_LEN_LSUB_CTX: AtomicU64 = AtomicU64::new(0);
static FP_NONPTR_TRUE: AtomicU64 = AtomicU64::new(0);

pub fn print_pi_body_free_provenance() {
    if std::env::var_os("MG_PI_FREE_PROV").is_none() { return; }
    macro_rules! p { ($n:literal,$x:expr) => { eprintln!("MG_PI_FREE {}={}", $n, $x.load(Relaxed)); }; }
    p!("enter", FP_ENTER); p!("body_same", FP_BODY_SAME); p!("env_ptr_same", FP_ENV_PTR_SAME);
    p!("env_hash_same", FP_ENV_HASH_SAME); p!("env_len_same", FP_ENV_LEN_SAME); p!("lsub_ptr_same", FP_LSUB_PTR_SAME);
    p!("ctx_ptr_same", FP_CTX_PTR_SAME); p!("domain_ptr_same", FP_DOMAIN_PTR_SAME);
    p!("body_hash", FP_BODY_HASH); p!("body_hash_len", FP_BODY_HASH_LEN);
    p!("body_hash_len_lsub", FP_BODY_HASH_LEN_LSUB); p!("body_hash_len_lsub_ctx", FP_BODY_HASH_LEN_LSUB_CTX);
    p!("post_ptr", FP_POST_PTR); p!("post_ptr_body_hash", FP_POST_PTR_BODY_HASH);
    p!("post_ptr_body_hash_len", FP_POST_PTR_BODY_HASH_LEN); p!("post_ptr_body_hash_len_lsub", FP_POST_PTR_BODY_HASH_LEN_LSUB);
    p!("post_ptr_body_hash_len_lsub_ctx", FP_POST_PTR_BODY_HASH_LEN_LSUB_CTX); p!("nonptr_true", FP_NONPTR_TRUE);
}
'''
if anchor not in s: raise SystemExit('import anchor missing')
s=s.replace(anchor,anchor+insert,1)
old='''                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                self.unify::<RIGID>(depth + 1, vx, vy)'''
new='''                if !self.unify::<RIGID>(depth, dx, dy) {\n                    return false;\n                }\n                FP_ENTER.fetch_add(1, Relaxed);\n                let body_same = bx.body == by.body;\n                let env_ptr_same = std::ptr::eq(bx.env, by.env);\n                let env_hash_same = bx.env.get_hash() == by.env.get_hash();\n                let env_len_same = bx.env.len() == by.env.len();\n                let lsub_ptr_same = match (bx.env.lsub(), by.env.lsub()) {\n                    (None, None) => true,\n                    (Some(a), Some(b)) => std::ptr::eq(a, b),\n                    _ => false,\n                };\n                let ctx_ptr_same = match (bx.ctx, by.ctx) {\n                    (None, None) => true,\n                    (Some(a), Some(b)) => std::ptr::eq(a, b),\n                    _ => false,\n                };\n                let domain_ptr_same = std::ptr::eq(*dx, *dy);\n                let body_hash = body_same && env_hash_same;\n                let body_hash_len = body_hash && env_len_same;\n                let body_hash_len_lsub = body_hash_len && lsub_ptr_same;\n                let body_hash_len_lsub_ctx = body_hash_len_lsub && ctx_ptr_same;\n                if body_same { FP_BODY_SAME.fetch_add(1, Relaxed); }\n                if env_ptr_same { FP_ENV_PTR_SAME.fetch_add(1, Relaxed); }\n                if env_hash_same { FP_ENV_HASH_SAME.fetch_add(1, Relaxed); }\n                if env_len_same { FP_ENV_LEN_SAME.fetch_add(1, Relaxed); }\n                if lsub_ptr_same { FP_LSUB_PTR_SAME.fetch_add(1, Relaxed); }\n                if ctx_ptr_same { FP_CTX_PTR_SAME.fetch_add(1, Relaxed); }\n                if domain_ptr_same { FP_DOMAIN_PTR_SAME.fetch_add(1, Relaxed); }\n                if body_hash { FP_BODY_HASH.fetch_add(1, Relaxed); }\n                if body_hash_len { FP_BODY_HASH_LEN.fetch_add(1, Relaxed); }\n                if body_hash_len_lsub { FP_BODY_HASH_LEN_LSUB.fetch_add(1, Relaxed); }\n                if body_hash_len_lsub_ctx { FP_BODY_HASH_LEN_LSUB_CTX.fetch_add(1, Relaxed); }\n                let dx = *dx;\n                let fresh = self.mk_bvar_hc(depth, dx);\n                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                let post_ptr = std::ptr::eq(vx, vy);\n                if post_ptr {\n                    FP_POST_PTR.fetch_add(1, Relaxed);\n                    if body_hash { FP_POST_PTR_BODY_HASH.fetch_add(1, Relaxed); }\n                    if body_hash_len { FP_POST_PTR_BODY_HASH_LEN.fetch_add(1, Relaxed); }\n                    if body_hash_len_lsub { FP_POST_PTR_BODY_HASH_LEN_LSUB.fetch_add(1, Relaxed); }\n                    if body_hash_len_lsub_ctx { FP_POST_PTR_BODY_HASH_LEN_LSUB_CTX.fetch_add(1, Relaxed); }\n                }\n                let r = self.unify::<RIGID>(depth + 1, vx, vy);\n                if !post_ptr && r { FP_NONPTR_TRUE.fetch_add(1, Relaxed); }\n                r'''
if old not in s: raise SystemExit('Pi body anchor missing')
s=s.replace(old,new,1)
conv.write_text(s)
main=Path('kernel/src/main.rs'); m=main.read_text()
oldm='''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
newm='''    sokonanoda::conv::print_pi_body_free_provenance();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if oldm not in m: raise SystemExit('main anchor missing')
main.write_text(m.replace(oldm,newm,1))
print('patched Pi-body free provenance census')
