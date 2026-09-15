from pathlib import Path

# Diagnostic-only localization of already-earned false splits by Value class.
# No production frame or canonicalization behavior is changed.

p=Path("a6/src/util.rs")
s=p.read_text()
field_marker="    pub(crate) frames: hashbrown::HashTable<E<'a>>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_kind_seen: "
    "FxHashMap<(u64, usize, Vec<usize>), (Vec<usize>, Vec<u8>)>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)
init_marker="            frames: hashbrown::HashTable::with_capacity(SESSION_MAP_CAP),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_kind_seen: FxHashMap::default(),\n",1)
clear_marker="        self.frames.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_kind_seen.clear();\n",1)
session_marker="""        if self.frames.capacity() > KEEP_CAP {
            self.frames = hashbrown::HashTable::new();
        } else {
            self.frames.clear();
        }
"""
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_map(&mut self.cq_kind_seen);\n",1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)
marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static CK_CALLS: AtomicU64 = AtomicU64::new(0);
static CK_FALSE_FRAMES: AtomicU64 = AtomicU64::new(0);
static CK_FALSE_SIMPLE_ONLY: AtomicU64 = AtomicU64::new(0);
static CK_FALSE_STRUCTURAL: AtomicU64 = AtomicU64::new(0);

static CK_ELIG_LAM: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_PI: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_SORT: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_NAT: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_STR: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_RIGID: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_UNFOLD: AtomicU64 = AtomicU64::new(0);
static CK_ELIG_THUNK: AtomicU64 = AtomicU64::new(0);

static CK_FS_LAM: AtomicU64 = AtomicU64::new(0);
static CK_FS_PI: AtomicU64 = AtomicU64::new(0);
static CK_FS_SORT: AtomicU64 = AtomicU64::new(0);
static CK_FS_NAT: AtomicU64 = AtomicU64::new(0);
static CK_FS_STR: AtomicU64 = AtomicU64::new(0);
static CK_FS_RIGID: AtomicU64 = AtomicU64::new(0);
static CK_FS_UNFOLD: AtomicU64 = AtomicU64::new(0);
static CK_FS_THUNK: AtomicU64 = AtomicU64::new(0);

#[inline]
fn cq_kind(v: V<'_>) -> u8 {
    match v {
        Value::Lam { .. } => 0,
        Value::Pi { .. } => 1,
        Value::Sort { .. } => 2,
        Value::NatLit { .. } => 3,
        Value::StrLit { .. } => 4,
        Value::Rigid { .. } => 5,
        Value::Unfold { .. } => 6,
        Value::Thunk { .. } => 7,
    }
}

#[inline]
fn cq_inc_elig(k: u8) {
    match k {
        0 => { CK_ELIG_LAM.fetch_add(1, Relaxed); }
        1 => { CK_ELIG_PI.fetch_add(1, Relaxed); }
        2 => { CK_ELIG_SORT.fetch_add(1, Relaxed); }
        3 => { CK_ELIG_NAT.fetch_add(1, Relaxed); }
        4 => { CK_ELIG_STR.fetch_add(1, Relaxed); }
        5 => { CK_ELIG_RIGID.fetch_add(1, Relaxed); }
        6 => { CK_ELIG_UNFOLD.fetch_add(1, Relaxed); }
        7 => { CK_ELIG_THUNK.fetch_add(1, Relaxed); }
        _ => unreachable!(),
    }
}

#[inline]
fn cq_inc_fs(k: u8) {
    match k {
        0 => { CK_FS_LAM.fetch_add(1, Relaxed); }
        1 => { CK_FS_PI.fetch_add(1, Relaxed); }
        2 => { CK_FS_SORT.fetch_add(1, Relaxed); }
        3 => { CK_FS_NAT.fetch_add(1, Relaxed); }
        4 => { CK_FS_STR.fetch_add(1, Relaxed); }
        5 => { CK_FS_RIGID.fetch_add(1, Relaxed); }
        6 => { CK_FS_UNFOLD.fetch_add(1, Relaxed); }
        7 => { CK_FS_THUNK.fetch_add(1, Relaxed); }
        _ => unreachable!(),
    }
}

pub fn print_cq_kind_stats() {
    eprintln!(
        "CQ_KIND calls={} false_frames={} simple_only={} structural={} elig_lam={} elig_pi={} elig_sort={} elig_nat={} elig_str={} elig_rigid={} elig_unfold={} elig_thunk={} fs_lam={} fs_pi={} fs_sort={} fs_nat={} fs_str={} fs_rigid={} fs_unfold={} fs_thunk={}",
        CK_CALLS.load(Relaxed),
        CK_FALSE_FRAMES.load(Relaxed),
        CK_FALSE_SIMPLE_ONLY.load(Relaxed),
        CK_FALSE_STRUCTURAL.load(Relaxed),
        CK_ELIG_LAM.load(Relaxed),
        CK_ELIG_PI.load(Relaxed),
        CK_ELIG_SORT.load(Relaxed),
        CK_ELIG_NAT.load(Relaxed),
        CK_ELIG_STR.load(Relaxed),
        CK_ELIG_RIGID.load(Relaxed),
        CK_ELIG_UNFOLD.load(Relaxed),
        CK_ELIG_THUNK.load(Relaxed),
        CK_FS_LAM.load(Relaxed),
        CK_FS_PI.load(Relaxed),
        CK_FS_SORT.load(Relaxed),
        CK_FS_NAT.load(Relaxed),
        CK_FS_STR.load(Relaxed),
        CK_FS_RIGID.load(Relaxed),
        CK_FS_UNFOLD.load(Relaxed),
        CK_FS_THUNK.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();
        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
"""
new="""        let slots: &[V<'t>] = unsafe { std::slice::from_raw_parts(buf.as_ptr().cast::<V<'t>>(), n) };
        let lsub = e.lsub();

        CK_CALLS.fetch_add(1, Relaxed);
        let raw_ptrs: Vec<usize> =
            slots.iter().map(|v| *v as *const Value<'t> as usize).collect();
        let raw_kinds: Vec<u8> = slots.iter().copied().map(cq_kind).collect();
        let earned_values: Vec<V<'t>> = slots.iter().copied().map(|v| {
            if v.is_canonical() {
                v
            } else {
                let key = v as *const Value<'t> as usize;
                self.tc_cache.canon_cache.get(&key).copied().unwrap_or(v)
            }
        }).collect();
        let earned_ptrs: Vec<usize> =
            earned_values.iter().map(|v| *v as *const Value<'t> as usize).collect();

        for ((raw, earned), kind) in raw_ptrs.iter().zip(&earned_ptrs).zip(&raw_kinds) {
            if raw != earned { cq_inc_elig(*kind); }
        }

        let lsub_addr = lsub.map_or(0, |l| l as *const value::LevelSub<'t> as usize);
        let diag_key = (out_mask, lsub_addr, earned_ptrs);
        match self.tc_cache.cq_kind_seen.entry(diag_key) {
            std::collections::hash_map::Entry::Occupied(o) => {
                let (first_ptrs, first_kinds) = o.get();
                if first_ptrs != &raw_ptrs {
                    CK_FALSE_FRAMES.fetch_add(1, Relaxed);
                    let mut only_simple = true;
                    for i in 0..raw_ptrs.len() {
                        if first_ptrs[i] != raw_ptrs[i] {
                            let k = raw_kinds[i];
                            cq_inc_fs(k);
                            let fk = first_kinds[i];
                            if fk != k { cq_inc_fs(fk); }
                            if !matches!(k, 2 | 3 | 4) || !matches!(fk, 2 | 3 | 4) {
                                only_simple = false;
                            }
                        }
                    }
                    if only_simple {
                        CK_FALSE_SIMPLE_ONLY.fetch_add(1, Relaxed);
                    } else {
                        CK_FALSE_STRUCTURAL.fetch_add(1, Relaxed);
                    }
                }
            }
            std::collections::hash_map::Entry::Vacant(v) => {
                v.insert((raw_ptrs, raw_kinds));
            }
        }

        let hash = out_mask.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(slots_hash);
        let r = self.intern_frame(hash, out_mask, slots, lsub);
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
new="""    if std::env::var_os("SOKONANODA_CQ_KIND_DIAG").is_some() {
        sokonanoda::eval::print_cq_kind_stats();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
