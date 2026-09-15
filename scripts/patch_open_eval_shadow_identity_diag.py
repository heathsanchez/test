from pathlib import Path

# Diagnostic-only shadow open-eval identity.
#
# Real open_eval_cache remains keyed by raw Env pointer and behaves unchanged.
# On REAL cache misses only, compute a semantic environment signature using
# already-earned canonical representatives and ask whether that (expr, signature)
# has been evaluated before. A shadow hit is therefore a cache-reuse opportunity
# blocked only by raw environment identity.
#
# No cached value is returned from the shadow structure.

p=Path("a6/src/util.rs")
s=p.read_text()
field_marker="    pub(crate) open_eval_seen: FxHashSet<ExprPtr<'t>>,\n"
field_insert=field_marker+(
    "    pub(crate) cq_open_shadow: "
    "FxHashSet<(ExprPtr<'t>, u64, usize, Vec<usize>)>,\n"
)
assert field_marker in s
s=s.replace(field_marker,field_insert,1)
init_marker="            open_eval_seen: small_fx_hash_set(),\n"
assert init_marker in s
s=s.replace(init_marker,init_marker+"            cq_open_shadow: FxHashSet::default(),\n",1)
clear_marker="        self.open_eval_seen.clear();\n"
assert clear_marker in s
s=s.replace(clear_marker,clear_marker+"        self.cq_open_shadow.clear();\n",1)
session_marker="        shrink_set(&mut self.open_eval_seen);\n"
assert session_marker in s
s=s.replace(session_marker,session_marker+"        shrink_set(&mut self.cq_open_shadow);\n",1)
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
static OE_RAW_HIT: AtomicU64 = AtomicU64::new(0);
static OE_RAW_MISS: AtomicU64 = AtomicU64::new(0);
static OE_SHADOW_HIT: AtomicU64 = AtomicU64::new(0);
static OE_SHADOW_PROJ: AtomicU64 = AtomicU64::new(0);
static OE_SHADOW_LET: AtomicU64 = AtomicU64::new(0);
static OE_SHADOW_PI: AtomicU64 = AtomicU64::new(0);

pub fn print_open_eval_shadow_stats() {
    eprintln!(
        "OPEN_EVAL_SHADOW raw_hit={} raw_miss={} shadow_hit={} shadow_proj={} shadow_let={} shadow_pi={}",
        OE_RAW_HIT.load(Relaxed),
        OE_RAW_MISS.load(Relaxed),
        OE_SHADOW_HIT.load(Relaxed),
        OE_SHADOW_PROJ.load(Relaxed),
        OE_SHADOW_LET.load(Relaxed),
        OE_SHADOW_PI.load(Relaxed),
    );
}
"""
assert marker in s
s=s.replace(marker,insert,1)

old="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }
            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            return v;
"""
new="""            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                OE_RAW_HIT.fetch_add(1, Relaxed);
                return v;
            }
            OE_RAW_MISS.fetch_add(1, Relaxed);

            // Shadow identity only. Never use it to answer eval.
            let (smask, slsub, sslots): (u64, usize, Vec<usize>) = match te {
                value::Env::Framed { mask, slots, .. } => {
                    let ps = slots.iter().map(|v| {
                        let raw = *v;
                        let rep = if raw.is_canonical() {
                            raw
                        } else {
                            let k = raw as *const Value<'t> as usize;
                            self.tc_cache.canon_cache.get(&k).copied().unwrap_or(raw)
                        };
                        rep as *const Value<'t> as usize
                    }).collect();
                    (*mask, te.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize), ps)
                }
                value::Env::Nil { .. } =>
                    (0, te.lsub().map_or(0, |l| l as *const value::LevelSub<'t> as usize), Vec::new()),
                value::Env::Cons { .. } =>
                    (u64::MAX, te as *const value::Env<'t> as usize, Vec::new()),
            };
            let skey = (e, smask, slsub, sslots);
            if self.tc_cache.cq_open_shadow.contains(&skey) {
                OE_SHADOW_HIT.fetch_add(1, Relaxed);
                match self.ctx.read_expr_ref(e) {
                    Expr::Proj { .. } => { OE_SHADOW_PROJ.fetch_add(1, Relaxed); }
                    Expr::Let { .. } => { OE_SHADOW_LET.fetch_add(1, Relaxed); }
                    Expr::Pi { .. } => { OE_SHADOW_PI.fetch_add(1, Relaxed); }
                    _ => {}
                }
            }

            let v = self.eval_no_cache(depth, te, e);
            self.tc_cache.open_eval_cache.insert(key, v);
            self.tc_cache.cq_open_shadow.insert(skey);
            return v;
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
new="""    if std::env::var_os("SOKONANODA_OPEN_EVAL_SHADOW").is_some() {
        sokonanoda::eval::print_open_eval_shadow_stats();
    }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s
p.write_text(s.replace(old,new,1))
