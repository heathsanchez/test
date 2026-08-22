from pathlib import Path
import os

mode=os.environ['MG_CLOSURE_MODE']
p=Path(os.environ.get('KERNEL_DIR','kernel-reuse'))/'src/eval.rs'
s=p.read_text()
old='''        let env = value::env_extend(self.arena, clo.env, v);\n        match clo.ctx {\n            None => self.eval(depth, env, clo.body),\n            Some(clo_ctx) => {'''
if mode == 'keyonly':
    new='''        let env = value::env_extend(self.arena, clo.env, v);\n        match clo.ctx {\n            None => {\n                if clo.body.num_loose_bvars() > 0 {\n                    let _observed_env = self.key_env(env, clo.body);\n                }\n                self.eval(depth, env, clo.body)\n            },\n            Some(clo_ctx) => {'''
elif mode == 'reuse':
    new='''        let env = value::env_extend(self.arena, clo.env, v);\n        match clo.ctx {\n            None => {\n                if clo.body.num_loose_bvars() == 0 && env.lsub().is_none() {\n                    return self.eval(depth, env, clo.body);\n                }\n                let te = self.key_env(env, clo.body);\n                let key = (te as *const value::Env<'t> as usize, clo.body);\n                if let Some(v) = self.tc_cache.open_eval_cache.get(&key) {\n                    return v;\n                }\n                let out = self.eval_no_cache(depth, te, clo.body);\n                self.tc_cache.open_eval_cache.insert(key, out);\n                out\n            },\n            Some(clo_ctx) => {'''
else:
    raise SystemExit(mode)
if old not in s:
    raise SystemExit('apply_closure anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('patched',mode,p)
