from pathlib import Path
import difflib,json,hashlib
R=Path(__file__).resolve().parent;source=R/'trace/metatron-kernel';p=source/'src/convert.rs';s=p.read_text();(R/'skip-convert.rs').write_text(s)
a=s.index('fn source_avoids_capture_uncached(');b=s.index('\n#[cfg(test)]',a);piece=s[a:b]
piece=piece.replace('vec![(body.clone(), virtual_slots)]','vec![(body.clone(), virtual_slots, false)]').replace('while let Some((source, virtual_slots)) = pending.pop() {','''while let Some((source, virtual_slots, finish)) = pending.pop() {
        if finish { capture_opportunity::retain(&source,virtual_slots,free); continue; }
        capture_opportunity::observe(&source,virtual_slots,free);
''')
needle='''        if !visited.insert((source.expr, source.env.id(), virtual_slots)) { continue; }''';assert piece.count(needle)==1;piece=piece.replace(needle,needle+'\n        pending.push((source.clone(),virtual_slots,true));')
piece=piece.replace('pending.push((captured.clone(), 0))','pending.push((captured.clone(), 0, false))').replace('(c.clone(), 0))','(c.clone(), 0, false))');s=s[:a]+piece+s[b:]
s+='''
// Diagnostic observer: never skips or changes a semantic traversal.
#[cfg(feature="diagnostics")]
pub(crate) mod capture_opportunity {
 use super::*;use std::cell::RefCell;
 type Key=(ExprId,u64,usize,u64,FreeId);
 #[derive(Default)]struct State{calls:u64,hits:u64,stores:u64,root_hits:u64,seen:HashMap<Key,Closure>}
 thread_local!{static STATE:RefCell<State>=RefCell::new(State::default());}
 fn key(c:&Closure,v:u64,f:FreeId)->Key{(c.expr,c.env.id(),c.levels.identity(),v,f)}
 pub(super)fn observe(c:&Closure,v:u64,f:FreeId){if !crate::diagnostics::receiver_target_active(){return}STATE.with_borrow_mut(|s|{s.calls+=1;if s.seen.contains_key(&key(c,v,f)){s.hits+=1;if v==1{s.root_hits+=1}}});}
 pub(super)fn retain(c:&Closure,v:u64,f:FreeId){if !crate::diagnostics::receiver_target_active(){return}STATE.with_borrow_mut(|s|{let k=key(c,v,f);if s.seen.len()<8192&&!s.seen.contains_key(&k){s.seen.insert(k,c.clone());s.stores+=1;}});}
 pub(crate)struct Scope(pub bool);impl Drop for Scope{fn drop(&mut self){if self.0{STATE.with_borrow(|s|eprintln!("CAPTURE_OPPORTUNITY:calls={}:hits={}:root_hits={}:stores={}:entries={}:diagnostic_only=true:no_skipping=true",s.calls,s.hits,s.root_hits,s.stores,s.seen.len()));}}}
}
''';p.write_text(s)
p=source/'src/checker.rs';s=p.read_text();needle='''        crate::diagnostics::receiver_target(matches!(&declaration,Declaration::Theorem{name,..} if name.0==26089));''';assert s.count(needle)==1;s=s.replace(needle,needle+'''
        #[cfg(feature="diagnostics")]
        let _capture_probe_summary=crate::convert::capture_opportunity::Scope(matches!(&declaration,Declaration::Theorem{name,..} if name.0==26089));''');p.write_text(s)
# The observer is compile-only; capture_opportunity calls deliberately require diagnostics.
patch=''
for rel in ['src/convert.rs','src/checker.rs','src/diagnostics.rs']:
 patch+=''.join(difflib.unified_diff((R/'extracted/metatron-kernel'/rel).read_text().splitlines(True),(source/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(R/'capture-probe.patch').write_text(patch);print(json.dumps(dict(patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),diagnostic_only=True)))
