from pathlib import Path
p=Path('a3/src/eval.rs')
s=p.read_text()
needle='use std::collections::hash_map::Entry;\n'
assert needle in s
s=s.replace(needle, needle+'use std::sync::atomic::{AtomicU64, Ordering::Relaxed};\nstatic KEY_ENV_SAMPLE: AtomicU64 = AtomicU64::new(0);\n',1)
old='''    #[inline]\n    pub(crate) fn key_env(&mut self, env: E<'t>, e: ExprPtr<'t>) -> E<'t> {\n        let k = e.num_loose_bvars();\n'''
new='''    #[inline]\n    #[track_caller]\n    pub(crate) fn key_env(&mut self, env: E<'t>, e: ExprPtr<'t>) -> E<'t> {\n        let sample = KEY_ENV_SAMPLE.fetch_add(1, Relaxed);\n        if sample & 1023 == 0 {\n            let loc = std::panic::Location::caller();\n            eprintln!("KEYENV_CALLER {}:{}", loc.file(), loc.line());\n        }\n        let k = e.num_loose_bvars();\n'''
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
