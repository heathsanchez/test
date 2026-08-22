from pathlib import Path

conv = Path('kernel-census/src/eval.rs')
s = conv.read_text()
anchor = 'use std::cell::OnceCell;\n'
insert = r'''use std::sync::atomic::{AtomicU64, Ordering::Relaxed};

static MG_REC_FIRE: AtomicU64 = AtomicU64::new(0);
static MG_REC_CACHE_HIT: AtomicU64 = AtomicU64::new(0);
static MG_REC_CACHE_MISS: AtomicU64 = AtomicU64::new(0);
static MG_REC_RULE_LAM: AtomicU64 = AtomicU64::new(0);
static MG_REC_EXPECTED_BINDERS: AtomicU64 = AtomicU64::new(0);
static MG_REC_SYNTACTIC_BINDERS: AtomicU64 = AtomicU64::new(0);
static MG_REC_EXTRA_ARGS: AtomicU64 = AtomicU64::new(0);
static MG_REC_NAT_FAST: AtomicU64 = AtomicU64::new(0);

pub fn print_recursor_10565_census() {
    if std::env::var_os("MG_REC_CENSUS").is_none() { return; }
    macro_rules! p { ($n:literal,$x:expr) => { eprintln!("MG_REC10565 {}={}", $n, $x.load(Relaxed)); }; }
    p!("fire", MG_REC_FIRE);
    p!("cache_hit", MG_REC_CACHE_HIT);
    p!("cache_miss", MG_REC_CACHE_MISS);
    p!("rule_value_lam", MG_REC_RULE_LAM);
    p!("expected_binders", MG_REC_EXPECTED_BINDERS);
    p!("syntactic_binders", MG_REC_SYNTACTIC_BINDERS);
    p!("extra_args", MG_REC_EXTRA_ARGS);
    p!("nat_fast", MG_REC_NAT_FAST);
}
'''
if anchor not in s: raise SystemExit('import anchor missing')
s=s.replace(anchor,anchor+insert,1)

old='''        if self.ctx.export_file.config.nat_extension
            && rec.all_inductives.first().copied() == self.ctx.export_file.name_cache.nat
        {
            if let Value::NatLit { ptr , ..} = major {
                return Some(self.nat_rec_natlit(depth, args, *ptr, rec, levels));
            }
        }'''
new='''        MG_REC_FIRE.fetch_add(1, Relaxed);
        if self.ctx.export_file.config.nat_extension
            && rec.all_inductives.first().copied() == self.ctx.export_file.name_cache.nat
        {
            if let Value::NatLit { ptr , ..} = major {
                MG_REC_NAT_FAST.fetch_add(1, Relaxed);
                return Some(self.nat_rec_natlit(depth, args, *ptr, rec, levels));
            }
        }'''
if old not in s: raise SystemExit('fire anchor missing')
s=s.replace(old,new,1)

old2='''        let cache_key = (rec_rule.val, levels);
        let mut result = match self.tc_cache.rec_rule_cache.get(&cache_key) {
            Some(v) => *v,
            None => {
                let v = self.eval_inst(rec_rule.val, rec.info.uparams, levels);
                self.tc_cache.rec_rule_cache.insert(cache_key, v);
                v
            }
        };
        let nprefix = usize::from(rec.num_params + rec.num_motives + rec.num_minors);
        result = self.apply_many(depth, result, &args[..nprefix]);
        result = self.apply_many(depth, result, &ctor_args[num_extra..]);
        result = self.apply_many(depth, result, &args[rec.major_idx() + 1..]);'''
new2='''        let cache_key = (rec_rule.val, levels);
        let mut result = match self.tc_cache.rec_rule_cache.get(&cache_key) {
            Some(v) => { MG_REC_CACHE_HIT.fetch_add(1, Relaxed); *v },
            None => {
                MG_REC_CACHE_MISS.fetch_add(1, Relaxed);
                let v = self.eval_inst(rec_rule.val, rec.info.uparams, levels);
                self.tc_cache.rec_rule_cache.insert(cache_key, v);
                v
            }
        };
        if matches!(result, Value::Lam { .. }) { MG_REC_RULE_LAM.fetch_add(1, Relaxed); }
        let nprefix = usize::from(rec.num_params + rec.num_motives + rec.num_minors);
        let nfields = ctor_args.len() - num_extra;
        let expected = nprefix + nfields;
        MG_REC_EXPECTED_BINDERS.fetch_add(expected as u64, Relaxed);
        MG_REC_EXTRA_ARGS.fetch_add(args.len().saturating_sub(rec.major_idx() + 1) as u64, Relaxed);
        let mut e = rec_rule.val;
        let mut syn = 0usize;
        while syn < expected {
            match self.ctx.read_expr(e) {
                Expr::Lambda { body, .. } => { syn += 1; e = body; }
                _ => break,
            }
        }
        MG_REC_SYNTACTIC_BINDERS.fetch_add(syn as u64, Relaxed);
        result = self.apply_many(depth, result, &args[..nprefix]);
        result = self.apply_many(depth, result, &ctor_args[num_extra..]);
        result = self.apply_many(depth, result, &args[rec.major_idx() + 1..]);'''
if old2 not in s: raise SystemExit('rec rule anchor missing')
s=s.replace(old2,new2,1)
Path('kernel-census/src/eval.rs').write_text(s)

m=Path('kernel-census/src/main.rs')
ms=m.read_text()
anchor_m='''    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
new_m='''    sokonanoda::eval::print_recursor_10565_census();\n    // Pretty print as necessary\n    let pp_errs = export_file.pp_selected_declars(pp_destination.as_mut());'''
if anchor_m not in ms: raise SystemExit('main anchor missing')
ms=ms.replace(anchor_m,new_m,1)
m.write_text(ms)
print('patched recursor census')
