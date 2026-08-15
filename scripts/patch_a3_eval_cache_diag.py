from pathlib import Path

SESSION_BUDGET=2_621_440
p=Path('a3/src/tc.rs'); s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'; assert old in s; p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))
p=Path('a3/src/eval.rs'); s=p.read_text()
# Apply A3.
old="""                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                let pruned = self.key_env(env, body);
                env = value::env_extend(self.arena, pruned, args[i]);
                body = inner;
                i += 1;
"""
new="""                let Expr::Lambda { body: inner, .. } = self.ctx.read_expr(body) else { break };
                env = value::env_extend(self.arena, env, args[i]);
                body = inner;
                i += 1;
"""
assert old in s; s=s.replace(old,new,1)
# Diagnostics.
s=s.replace('use std::cell::OnceCell;\n','use std::cell::OnceCell;\nuse std::sync::atomic::{AtomicU64, Ordering::Relaxed};\n',1)
marker="pub(crate) type SpineArgs<'t> = smallvec::SmallVec<[V<'t>; 8]>;\n"
insert=marker+"""
static OPEN_CALLS: [AtomicU64; 5] = [const { AtomicU64::new(0) }; 5];
static OPEN_HITS: [AtomicU64; 5] = [const { AtomicU64::new(0) }; 5];

#[inline]
fn open_kind(e: &Expr) -> usize {
    match e { Expr::App {..} => 0, Expr::Proj {..} => 1, Expr::Let {..} => 2, Expr::Pi {..} => 3, Expr::Lambda {..} => 4, _ => unreachable!() }
}
pub fn print_open_eval_stats() {
    let names=["app","proj","let","pi","lambda"];
    for i in 0..5 { eprintln!("OPEN_EVAL kind={} calls={} hits={}", names[i], OPEN_CALLS[i].load(Relaxed), OPEN_HITS[i].load(Relaxed)); }
}
"""
assert marker in s; s=s.replace(marker,insert,1)
old="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                return v;
            }
"""
new="""        if matches!(
            self.ctx.read_expr_ref(e),
            Expr::App { .. } | Expr::Proj { .. } | Expr::Let { .. } | Expr::Pi { .. } | Expr::Lambda { .. }
        ) {
            let ki = open_kind(self.ctx.read_expr_ref(e));
            OPEN_CALLS[ki].fetch_add(1, Relaxed);
            let te = self.key_env(env, e);
            let key = (te as *const value::Env<'t> as usize, e);
            if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {
                OPEN_HITS[ki].fetch_add(1, Relaxed);
                return v;
            }
"""
assert old in s; s=s.replace(old,new,1)
p.write_text(s)

p=Path('a3/src/main.rs'); s=p.read_text()
old="""    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
new="""    if std::env::var_os("SOKONANODA_EVAL_DIAG").is_some() { sokonanoda::eval::print_open_eval_stats(); }
    match out {
        Ok(Some(msg)) => println!("{}", msg),
        Ok(None) => {}
"""
assert old in s; p.write_text(s.replace(old,new,1))
