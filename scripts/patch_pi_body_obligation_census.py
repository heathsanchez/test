from pathlib import Path

conv = Path('kernel/src/conv.rs')
s = conv.read_text()

anchor = 'use crate::value::{self, ElimView, Env, RigidHead, Spine, UnfoldHead, Value, E, S, V};\n'
insert = r'''use std::collections::HashSet;
use std::sync::{Mutex, OnceLock};
use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static PB_ENTER: AtomicU64 = AtomicU64::new(0);
static PB_CLOSURE_PTR_EQ: AtomicU64 = AtomicU64::new(0);
static PB_RAW_PAIR_REPEAT: AtomicU64 = AtomicU64::new(0);
static PB_RAW_PAIR_UNIQUE: AtomicU64 = AtomicU64::new(0);
static PB_RIGID_RIGID: AtomicU64 = AtomicU64::new(0);
static PB_PI_PI: AtomicU64 = AtomicU64::new(0);
static PB_LAM_LAM: AtomicU64 = AtomicU64::new(0);
static PB_SORT_SORT: AtomicU64 = AtomicU64::new(0);
static PB_UNFOLD_UNFOLD: AtomicU64 = AtomicU64::new(0);
static PB_MIXED: AtomicU64 = AtomicU64::new(0);
static PB_BODY_UNIFY_TRUE: AtomicU64 = AtomicU64::new(0);
static PB_BODY_UNIFY_FALSE: AtomicU64 = AtomicU64::new(0);

static PB_SEEN: OnceLock<Mutex<HashSet<(usize, usize)>>> = OnceLock::new();

#[inline]
fn pb_shape(v: &Value<'_>) -> u8 {
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

#[inline]
fn pb_note_pair(x: &Value<'_>, y: &Value<'_>) {
    PB_ENTER.fetch_add(1, Relaxed);
    if std::ptr::eq(x, y) { PB_CLOSURE_PTR_EQ.fetch_add(1, Relaxed); }
    match (pb_shape(x), pb_shape(y)) {
        (0,0) => { PB_RIGID_RIGID.fetch_add(1, Relaxed); },
        (3,3) => { PB_PI_PI.fetch_add(1, Relaxed); },
        (2,2) => { PB_LAM_LAM.fetch_add(1, Relaxed); },
        (4,4) => { PB_SORT_SORT.fetch_add(1, Relaxed); },
        (1,1) => { PB_UNFOLD_UNFOLD.fetch_add(1, Relaxed); },
        _ => { PB_MIXED.fetch_add(1, Relaxed); },
    }
    let xa = x as *const Value<'_> as usize;
    let ya = y as *const Value<'_> as usize;
    let k = if xa <= ya { (xa,ya) } else { (ya,xa) };
    let seen = PB_SEEN.get_or_init(|| Mutex::new(HashSet::new()));
    let mut g = seen.lock().unwrap();
    if g.insert(k) { PB_RAW_PAIR_UNIQUE.fetch_add(1, Relaxed); }
    else { PB_RAW_PAIR_REPEAT.fetch_add(1, Relaxed); }
}

pub fn print_pi_body_obligation_census() {
    if std::env::var_os("MG_PI_BODY_CENSUS").is_none() { return; }
    macro_rules! p { ($n:literal,$x:expr) => { eprintln!("MG_PI_BODY {}={}", $n, $x.load(Relaxed)); }; }
    p!("enter", PB_ENTER);
    p!("closure_ptr_eq", PB_CLOSURE_PTR_EQ);
    p!("raw_pair_unique", PB_RAW_PAIR_UNIQUE);
    p!("raw_pair_repeat", PB_RAW_PAIR_REPEAT);
    p!("rigid_rigid", PB_RIGID_RIGID);
    p!("pi_pi", PB_PI_PI);
    p!("lam_lam", PB_LAM_LAM);
    p!("sort_sort", PB_SORT_SORT);
    p!("unfold_unfold", PB_UNFOLD_UNFOLD);
    p!("mixed", PB_MIXED);
    p!("body_unify_true", PB_BODY_UNIFY_TRUE);
    p!("body_unify_false", PB_BODY_UNIFY_FALSE);
}
'''
if anchor not in s: raise SystemExit('import anchor missing')
s = s.replace(anchor, anchor + insert, 1)

old = '''                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                self.unify::<RIGID>(depth + 1, vx, vy)'''
new = '''                let vx = self.apply_closure(depth + 1, bx, fresh, Some(dx));\n                let vy = self.apply_closure(depth + 1, by, fresh, Some(dx));\n                pb_note_pair(vx, vy);\n                let r = self.unify::<RIGID>(depth + 1, vx, vy);\n                if r { PB_BODY_UNIFY_TRUE.fetch_add(1, Relaxed); } else { PB_BODY_UNIFY_FALSE.fetch_add(1, Relaxed); }\n                r'''
if old not in s: raise SystemExit('Pi body anchor missing')
s = s.replace(old,new,1)
conv.write_text(s)

main = Path('kernel/src/main.rs')
m = main.read_text()
oldm = '''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
newm = '''    sokonanoda::conv::print_pi_body_obligation_census();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if oldm not in m: raise SystemExit('main anchor missing')
m = m.replace(oldm,newm,1)
main.write_text(m)
print('patched Pi-body obligation census')
