from pathlib import Path

# Diagnostic-only environment capacity retention atlas for current official
# sokonanoda. Production lookup, insertion, and clear behavior remains
# authoritative. We only count growth and capacity discarded at clear_session.

p=Path("a6/src/util.rs")
s=p.read_text()

marker="pub(crate) const KEEP_CAP: usize = 1 << 15;\n"
diag=r'''pub(crate) const KEEP_CAP: usize = 1 << 15;

static EC_SESSION_CLEARS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

static EC_WIDE_INSERTS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_WIDE_GROWTHS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_WIDE_MAX_CAP: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_WIDE_DISCARDS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_WIDE_MAX_DISCARD: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

static EC_ENV_INSERTS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_ENV_GROWTHS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_ENV_MAX_CAP: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_ENV_DISCARDS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_ENV_MAX_DISCARD: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

static EC_FRAME_INSERTS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_FRAME_GROWTHS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_FRAME_MAX_CAP: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_FRAME_DISCARDS: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
static EC_FRAME_MAX_DISCARD: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

#[inline]
fn ec_max(dst: &std::sync::atomic::AtomicU64, value: usize) {
    use std::sync::atomic::Ordering::Relaxed;
    dst.fetch_max(value as u64, Relaxed);
}

#[inline]
pub(crate) fn diag_wide_prune_insert(before_cap: usize, after_cap: usize) {
    use std::sync::atomic::Ordering::Relaxed;
    EC_WIDE_INSERTS.fetch_add(1, Relaxed);
    if after_cap > before_cap {
        EC_WIDE_GROWTHS.fetch_add(1, Relaxed);
    }
    ec_max(&EC_WIDE_MAX_CAP, after_cap);
}

#[inline]
pub(crate) fn diag_env_hc_insert(before_cap: usize, after_cap: usize) {
    use std::sync::atomic::Ordering::Relaxed;
    EC_ENV_INSERTS.fetch_add(1, Relaxed);
    if after_cap > before_cap {
        EC_ENV_GROWTHS.fetch_add(1, Relaxed);
    }
    ec_max(&EC_ENV_MAX_CAP, after_cap);
}

#[inline]
pub(crate) fn diag_frame_insert(before_cap: usize, after_cap: usize) {
    use std::sync::atomic::Ordering::Relaxed;
    EC_FRAME_INSERTS.fetch_add(1, Relaxed);
    if after_cap > before_cap {
        EC_FRAME_GROWTHS.fetch_add(1, Relaxed);
    }
    ec_max(&EC_FRAME_MAX_CAP, after_cap);
}

#[inline]
fn diag_discard(cap: usize, discards: &std::sync::atomic::AtomicU64, max_discard: &std::sync::atomic::AtomicU64) {
    use std::sync::atomic::Ordering::Relaxed;
    if cap > KEEP_CAP {
        discards.fetch_add(1, Relaxed);
        ec_max(max_discard, cap);
    }
}

pub(crate) fn diag_env_capacity_clear_session(wide_cap: usize, env_cap: usize, frame_cap: usize) {
    use std::sync::atomic::Ordering::Relaxed;
    EC_SESSION_CLEARS.fetch_add(1, Relaxed);
    ec_max(&EC_WIDE_MAX_CAP, wide_cap);
    ec_max(&EC_ENV_MAX_CAP, env_cap);
    ec_max(&EC_FRAME_MAX_CAP, frame_cap);
    diag_discard(wide_cap, &EC_WIDE_DISCARDS, &EC_WIDE_MAX_DISCARD);
    diag_discard(env_cap, &EC_ENV_DISCARDS, &EC_ENV_MAX_DISCARD);
    diag_discard(frame_cap, &EC_FRAME_DISCARDS, &EC_FRAME_MAX_DISCARD);
}

pub fn print_env_capacity_diag() {
    use std::sync::atomic::Ordering::Relaxed;
    eprintln!(
        "ENV_CAPACITY session_clears={} wide_inserts={} wide_growths={} wide_max_cap={} wide_discards={} wide_max_discard={} env_inserts={} env_growths={} env_max_cap={} env_discards={} env_max_discard={} frame_inserts={} frame_growths={} frame_max_cap={} frame_discards={} frame_max_discard={}",
        EC_SESSION_CLEARS.load(Relaxed),
        EC_WIDE_INSERTS.load(Relaxed),
        EC_WIDE_GROWTHS.load(Relaxed),
        EC_WIDE_MAX_CAP.load(Relaxed),
        EC_WIDE_DISCARDS.load(Relaxed),
        EC_WIDE_MAX_DISCARD.load(Relaxed),
        EC_ENV_INSERTS.load(Relaxed),
        EC_ENV_GROWTHS.load(Relaxed),
        EC_ENV_MAX_CAP.load(Relaxed),
        EC_ENV_DISCARDS.load(Relaxed),
        EC_ENV_MAX_DISCARD.load(Relaxed),
        EC_FRAME_INSERTS.load(Relaxed),
        EC_FRAME_GROWTHS.load(Relaxed),
        EC_FRAME_MAX_CAP.load(Relaxed),
        EC_FRAME_DISCARDS.load(Relaxed),
        EC_FRAME_MAX_DISCARD.load(Relaxed),
    );
}
'''
assert marker in s
s=s.replace(marker,diag,1)

clear_marker="""    pub(crate) fn clear_session(&mut self) {
        self.probe_depth = 0;
"""
clear_new="""    pub(crate) fn clear_session(&mut self) {
        crate::util::diag_env_capacity_clear_session(
            self.wide_prune.capacity(),
            self.env_hc.capacity(),
            self.frames.capacity(),
        );
        self.probe_depth = 0;
"""
assert clear_marker in s
s=s.replace(clear_marker,clear_new,1)
p.write_text(s)

p=Path("a6/src/eval.rs")
s=p.read_text()

old="""    pub(crate) fn env_extend(&mut self, parent: E<'t>, v: V<'t>) -> E<'t> {
        let key = (parent as *const value::Env<'t> as usize, v as *const Value<'t> as usize);
        match self.tc_cache.env_hc.entry(key) {
            Entry::Occupied(o) => o.get(),
            Entry::Vacant(slot) => slot.insert(value::env_extend(self.arena, parent, v)),
        }
    }
"""
new="""    pub(crate) fn env_extend(&mut self, parent: E<'t>, v: V<'t>) -> E<'t> {
        let key = (parent as *const value::Env<'t> as usize, v as *const Value<'t> as usize);
        if let Some(r) = self.tc_cache.env_hc.get(&key).copied() {
            return r;
        }
        let before_cap = self.tc_cache.env_hc.capacity();
        let r = value::env_extend(self.arena, parent, v);
        self.tc_cache.env_hc.insert(key, r);
        crate::util::diag_env_hc_insert(before_cap, self.tc_cache.env_hc.capacity());
        r
    }
"""
assert old in s
s=s.replace(old,new,1)

old="""        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        e
    }
"""
new="""        let before_cap = self.tc_cache.frames.capacity();
        self.tc_cache.frames.insert_unique(hash, e, |e| e.get_hash());
        crate::util::diag_frame_insert(before_cap, self.tc_cache.frames.capacity());
        e
    }
"""
assert old in s
s=s.replace(old,new,1)

old="""                    self.tc_cache.frames.insert_unique(hash, r, |r| r.get_hash());
                    r
"""
new="""                    let before_cap = self.tc_cache.frames.capacity();
                    self.tc_cache.frames.insert_unique(hash, r, |r| r.get_hash());
                    crate::util::diag_frame_insert(before_cap, self.tc_cache.frames.capacity());
                    r
"""
assert old in s
s=s.replace(old,new,1)

old="""        self.tc_cache.wide_prune.insert(key, r);
        r
"""
new="""        let before_len = self.tc_cache.wide_prune.len();
        let before_cap = self.tc_cache.wide_prune.capacity();
        self.tc_cache.wide_prune.insert(key, r);
        if self.tc_cache.wide_prune.len() > before_len {
            crate::util::diag_wide_prune_insert(before_cap, self.tc_cache.wide_prune.capacity());
        }
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
new="""    if std::env::var_os("SOKONANODA_ENV_CAPACITY_DIAG").is_some() {
        sokonanoda::util::print_env_capacity_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
