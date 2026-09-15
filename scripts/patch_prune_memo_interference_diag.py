from pathlib import Path

# Diagnostic only: quantify interaction between semantic frame sharing and the
# mutable one-entry Env::prune memo.
#
# Does not change prune decisions or results.

p=Path("a6/src/eval.rs")
s=p.read_text()
s=s.replace(
    "use std::cell::OnceCell;\n",
    "use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n",
    1,
)
marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static PM_REQ: AtomicU64 = AtomicU64::new(0);
static PM_FRAME_SELF: AtomicU64 = AtomicU64::new(0);
static PM_FRAME_LOCAL: AtomicU64 = AtomicU64::new(0);
static PM_CONS_LOCAL: AtomicU64 = AtomicU64::new(0);
static PM_FRAME_DM: AtomicU64 = AtomicU64::new(0);
static PM_CONS_DM: AtomicU64 = AtomicU64::new(0);
static PM_FRAME_COLD: AtomicU64 = AtomicU64::new(0);
static PM_CONS_COLD: AtomicU64 = AtomicU64::new(0);

pub fn print_prune_memo_diag() {
    eprintln!(
        "PRUNE_MEMO_DIAG req={} frame_self={} frame_local={} cons_local={} frame_dm={} cons_dm={} frame_cold={} cons_cold={}",
        PM_REQ.load(Relaxed),
        PM_FRAME_SELF.load(Relaxed),
        PM_FRAME_LOCAL.load(Relaxed),
        PM_CONS_LOCAL.load(Relaxed),
        PM_FRAME_DM.load(Relaxed),
        PM_CONS_DM.load(Relaxed),
        PM_FRAME_COLD.load(Relaxed),
        PM_CONS_COLD.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {
        if mask == 0 {
            return self.lsub_base(e.lsub());
        }
        match e {
            value::Env::Nil { .. } => return e,
            value::Env::Framed { mask: m, prune, .. } => {
                if *m & mask == *m {
                    return e
                }
                let (m, r) = prune.get();
                if m == mask {
                    if let Some(r) = r {
                        return r;
                    }
                }
            }
            value::Env::Cons { prune, .. } => {
                let (m, r) = prune.get();
                if m == mask {
                    if let Some(r) = r {
                        return r;
                    }
                }
            }
        }
        let slot = (((e as *const value::Env<'t> as usize as u64).wrapping_mul(0x9E3779B97F4A7C15)
            ^ mask.wrapping_mul(0xD6E8FEB86659FD93))
            >> crate::util::PRUNE_DM_SHIFT) as usize;
        let ent = self.tc_cache.prune_dm[slot];
        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } | value::Env::Framed { prune, .. } =>
                        prune.set((mask, Some(hit))),
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        self.prune_env_cold(e, mask, slot)
    }
"""
new="""    fn prune_env(&mut self, e: E<'t>, mask: u64) -> E<'t> {
        if mask == 0 {
            return self.lsub_base(e.lsub());
        }
        PM_REQ.fetch_add(1, Relaxed);
        match e {
            value::Env::Nil { .. } => return e,
            value::Env::Framed { mask: m, prune, .. } => {
                if *m & mask == *m {
                    PM_FRAME_SELF.fetch_add(1, Relaxed);
                    return e
                }
                let (m, r) = prune.get();
                if m == mask {
                    if let Some(r) = r {
                        PM_FRAME_LOCAL.fetch_add(1, Relaxed);
                        return r;
                    }
                }
            }
            value::Env::Cons { prune, .. } => {
                let (m, r) = prune.get();
                if m == mask {
                    if let Some(r) = r {
                        PM_CONS_LOCAL.fetch_add(1, Relaxed);
                        return r;
                    }
                }
            }
        }
        let slot = (((e as *const value::Env<'t> as usize as u64).wrapping_mul(0x9E3779B97F4A7C15)
            ^ mask.wrapping_mul(0xD6E8FEB86659FD93))
            >> crate::util::PRUNE_DM_SHIFT) as usize;
        let ent = self.tc_cache.prune_dm[slot];
        if ent.0 == e as *const value::Env<'t> as usize && ent.1 == mask {
            if let Some(hit) = ent.2 {
                match e {
                    value::Env::Cons { prune, .. } => {
                        PM_CONS_DM.fetch_add(1, Relaxed);
                        prune.set((mask, Some(hit)));
                    }
                    value::Env::Framed { prune, .. } => {
                        PM_FRAME_DM.fetch_add(1, Relaxed);
                        prune.set((mask, Some(hit)));
                    }
                    value::Env::Nil { .. } => {}
                }
                return hit;
            }
        }
        match e {
            value::Env::Framed { .. } => { PM_FRAME_COLD.fetch_add(1, Relaxed); }
            value::Env::Cons { .. } => { PM_CONS_COLD.fetch_add(1, Relaxed); }
            value::Env::Nil { .. } => {}
        }
        self.prune_env_cold(e, mask, slot)
    }
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
new="""    if std::env::var_os("SOKONANODA_PRUNE_MEMO_DIAG").is_some() {
        sokonanoda::eval::print_prune_memo_diag();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
