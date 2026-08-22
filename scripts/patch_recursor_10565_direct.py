from pathlib import Path
import os

root=Path(os.environ.get('KERNEL_DIR','kernel-direct'))
p=root/'src/eval.rs'
s=p.read_text()
old='''        let cache_key = (rec_rule.val, levels);
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
        result = self.apply_many(depth, result, &args[rec.major_idx() + 1..]);
        Some(result)'''
new='''        let nprefix = usize::from(rec.num_params + rec.num_motives + rec.num_minors);
        let field_args = &ctor_args[num_extra..];

        // Lean #10565 family: the recursor rule is reconstructed by this kernel.
        // Avoid first evaluating its leading lambda telescope to a Value::Lam only
        // to feed the known arguments back through generic application. We peel
        // exactly the expected Lambda syntax and evaluate the body under the
        // corresponding environment. If the expected invariant is absent, fall
        // back to the submitted path rather than assuming it unsafely.
        let mut direct_env = if rec.info.uparams == levels || self.ctx.read_levels(rec.info.uparams).is_empty() {
            self.empty_env()
        } else {
            if self.ctx.read_levels(rec.info.uparams).len() != self.ctx.read_levels(levels).len() {
                return None;
            }
            let ls = self.intern_level_sub(rec.info.uparams, levels);
            self.lsub_base(Some(ls))
        };
        let mut direct_body = rec_rule.val;
        let mut direct_ok = true;
        for a in args[..nprefix].iter().chain(field_args.iter()) {
            match self.ctx.read_expr(direct_body) {
                Expr::Lambda { body, .. } => {
                    direct_env = value::env_extend(self.arena, direct_env, *a);
                    direct_body = body;
                }
                _ => { direct_ok = false; break; }
            }
        }
        let mut result = if direct_ok {
            self.eval(depth, direct_env, direct_body)
        } else {
            let cache_key = (rec_rule.val, levels);
            let mut old = match self.tc_cache.rec_rule_cache.get(&cache_key) {
                Some(v) => *v,
                None => {
                    let v = self.eval_inst(rec_rule.val, rec.info.uparams, levels);
                    self.tc_cache.rec_rule_cache.insert(cache_key, v);
                    v
                }
            };
            old = self.apply_many(depth, old, &args[..nprefix]);
            self.apply_many(depth, old, field_args)
        };
        result = self.apply_many(depth, result, &args[rec.major_idx() + 1..]);
        Some(result)'''
if old not in s: raise SystemExit('recursor fire anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('patched direct recursor instantiation',root)
