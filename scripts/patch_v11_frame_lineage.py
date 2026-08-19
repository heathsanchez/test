#!/usr/bin/env python3
from pathlib import Path

p=Path('scripts/run_developmental_checker_span_v10.py')
s=p.read_text()
s=s.replace('results/developmental-checker-lineage-v10','results/developmental-checker-lineage-v11')
s=s.replace("'LIVE_PROPAGATED_LINEAGE_V10'","'LIVE_FRAME_LINEAGE_V11'")
s=s.replace('propagated provenance reaches the later failed declaration comparison','frame-propagated provenance reaches the later failed declaration comparison')

old_helpers='''thread_local! {
    static MG_PROV: RefCell<HashMap<usize,u64>> = RefCell::new(HashMap::new());
}
#[inline] fn mg_prov_get(v: V<'_>) -> u64 {
    MG_PROV.with(|m| *m.borrow().get(&(v as *const Value<'_> as usize)).unwrap_or(&0))
}
#[inline] fn mg_prov_add(v: V<'_>, bits: u64) {
    if bits == 0 { return; }
    MG_PROV.with(|m| { let mut m=m.borrow_mut(); let k=v as *const Value<'_> as usize; *m.entry(k).or_insert(0) |= bits; });
}
#[inline] fn mg_prov_inherit(out: V<'_>, src: V<'_>) { mg_prov_add(out, mg_prov_get(src)); }
'''
new_helpers='''thread_local! {
    static MG_PROV: RefCell<HashMap<usize,u64>> = RefCell::new(HashMap::new());
    static MG_PROV_STACK: RefCell<Vec<u64>> = RefCell::new(Vec::new());
}
#[inline] fn mg_prov_get(v: V<'_>) -> u64 {
    MG_PROV.with(|m| *m.borrow().get(&(v as *const Value<'_> as usize)).unwrap_or(&0))
}
#[inline] fn mg_prov_add(v: V<'_>, bits: u64) {
    if bits == 0 { return; }
    MG_PROV.with(|m| { let mut m=m.borrow_mut(); let k=v as *const Value<'_> as usize; *m.entry(k).or_insert(0) |= bits; });
}
#[inline] fn mg_prov_inherit(out: V<'_>, src: V<'_>) { mg_prov_add(out, mg_prov_get(src)); }
#[inline] fn mg_frame_push() { MG_PROV_STACK.with(|s| s.borrow_mut().push(0)); }
#[inline] fn mg_frame_mark(bits: u64) {
    if bits == 0 { return; }
    MG_PROV_STACK.with(|s| { if let Some(x)=s.borrow_mut().last_mut() { *x |= bits; } });
}
#[inline] fn mg_frame_finish<'a>(v: V<'a>) -> V<'a> {
    let bits=MG_PROV_STACK.with(|s| s.borrow_mut().pop().unwrap_or(0));
    mg_prov_add(v,bits);
    MG_PROV_STACK.with(|s| { if let Some(x)=s.borrow_mut().last_mut() { *x |= bits; } });
    v
}
'''
if old_helpers not in s: raise SystemExit('V10 provenance helper block missing')
s=s.replace(old_helpers,new_helpers,1)

# Mark the active infer frame whenever a projection result is created. Replace all embedded
# variants so the normal and deliberately faulty checker stay structurally matched.
s=s.replace('mg_prov_add(mg_proj_return, 1);\\n        eprintln!',
            'mg_prov_add(mg_proj_return, 1);\\n        mg_frame_mark(1);\\n        eprintln!')

# Insert generic propagation at the infer_value boundary. A child projection marks its frame;
# finishing the call attaches the accumulated bit to the returned Value and bubbles it to the parent.
write_anchor='    p.write_text(s)\n\ndef inject_projection_fault(src):'
frame_patch="""    infer_start='''        let key = (self.key_env(env, e) as *const value::Env<'t> as usize, e);\n        let scope = self.uparam_scope();'''
    infer_start_new='''        mg_frame_push();\n        let key = (self.key_env(env, e) as *const value::Env<'t> as usize, e);\n        let scope = self.uparam_scope();'''
    if infer_start not in s: raise RuntimeError('infer frame start anchor missing')
    s=s.replace(infer_start,infer_start_new,1)
    cache_old='''        if let Some(cached) = self.tc_cache.type_cache.get(&key).copied() {\n            if flag == InferOnly || cached.checked_under == scope {\n                return cached.result;\n            }\n        }'''
    cache_new='''        if let Some(cached) = self.tc_cache.type_cache.get(&key).copied() {\n            if flag == InferOnly || cached.checked_under == scope {\n                mg_frame_mark(mg_prov_get(cached.result));\n                return mg_frame_finish(cached.result);\n            }\n        }'''
    if cache_old not in s: raise RuntimeError('infer cache frame anchor missing')
    s=s.replace(cache_old,cache_new,1)
    end_old='''        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };\n        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });\n        r'''
    end_new='''        let checked_under = if flag == Check { scope } else { CheckScope::Unchecked };\n        self.tc_cache.type_cache.insert(key, CachedType { result: r, checked_under });\n        mg_frame_finish(r)'''
    if end_old not in s: raise RuntimeError('infer frame finish anchor missing')
    s=s.replace(end_old,end_new,1)
    p.write_text(s)

def inject_projection_fault(src):"""
if write_anchor not in s: raise SystemExit('V11 augment write anchor missing')
s=s.replace(write_anchor,frame_patch,1)

p.write_text(s)
print('patched V11 runner for frame-propagated causal lineage')
