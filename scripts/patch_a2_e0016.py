from pathlib import Path
SESSION_BUDGET=2_621_440
for root in ('a2','e0016'):
    p=Path(root)/'src/tc.rs'; s=p.read_text(); old='const SESSION_BUDGET: usize = 1 << 20;'; assert old in s
    p.write_text(s.replace(old,f'const SESSION_BUDGET: usize = {SESSION_BUDGET};',1))
p=Path('e0016/src/infer.rs'); s=p.read_text()
old="""        let key = (self.key_env(env, e) as *const value::Env<'t> as usize, e);\n        let scope = self.uparam_scope();"""
new="""        let canonical_env = self.key_env(env, e);\n        let key = (canonical_env as *const value::Env<'t> as usize, e);\n        let scope = self.uparam_scope();"""
assert old in s; s=s.replace(old,new,1)
old="""                let clo = Closure::mk_infer(self.key_env(env, e), ctx, body);"""
new="""                let clo = Closure::mk_infer(canonical_env, ctx, body);"""
assert old in s; s=s.replace(old,new,1)
p.write_text(s)
