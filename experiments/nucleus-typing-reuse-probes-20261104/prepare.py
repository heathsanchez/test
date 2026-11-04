from pathlib import Path
import argparse,shutil

def prepare(source,out,mode):
 assert mode in('first-exact','fifo-exact','fifo-semantic')
 shutil.copytree(source,out);p=out/'src/typecheck.rs';s=p.read_text()
 field='    source_opening_proofs: RefCell<HashMap<(ExprId,u64,usize,FreeId),Closure>>,';assert s.count(field)==1
 s=s.replace(field,field+'\n    #[cfg(feature="diagnostics")]\n    typing_reuse_probe:RefCell<ExactTypingReuseProbe>,')
 field='source_opening_proofs:RefCell::new(HashMap::new()),';assert s.count(field)==5
 s=s.replace(field,field+'\n            #[cfg(feature="diagnostics")]\n            typing_reuse_probe:RefCell::new(ExactTypingReuseProbe::default()),')
 old='''    fn infer_exact_closure_in_context(
        &self,
        term: &Closure,
        context: &[TypeValue],
        remaining: &mut usize,
        depth: usize,
    ) -> Option<TypeValue> {'''
 new='''    fn infer_exact_closure_in_context(&self,term:&Closure,context:&[TypeValue],remaining:&mut usize,depth:usize)->Option<TypeValue>{
        #[cfg(feature="diagnostics")]
        let probe=exact_typing_probe::begin(self,term,context,*remaining,depth);
        let result=self.infer_exact_closure_uncached(term,context,remaining,depth);
        #[cfg(feature="diagnostics")]
        exact_typing_probe::finish(self,probe,term,context,result.as_ref());
        result
    }
    fn infer_exact_closure_uncached(
        &self,
        term: &Closure,
        context: &[TypeValue],
        remaining: &mut usize,
        depth: usize,
    ) -> Option<TypeValue> {'''
 assert s.count(old)==1;s=s.replace(old,new)
 key='(Closure,bool,Vec<Closure>)'if mode=='fifo-semantic'else'(ExprId,u64,usize,bool,Vec<(ExprId,u64,usize)>)'
 push='scope.push(t.clone());'if mode=='fifo-semantic'else'scope.push((t.expr,t.env.id(),t.levels.identity()));'
 make='(term.clone(),c.strict_origin_probe,scope)'if mode=='fifo-semantic'else'(term.expr,term.env.id(),term.levels.identity(),c.strict_origin_probe,scope)'
 capacity='return;'if mode=='first-exact'else'if let Some(old)=table.order.pop_front(){table.positive.remove(&old);}else{return;}'
 template='''
#[cfg(feature="diagnostics")]
#[derive(Default)]
struct ExactTypingReuseProbe{positive:HashMap<exact_typing_probe::Key,(Closure,Vec<Closure>,usize)>,order:std::collections::VecDeque<exact_typing_probe::Key>}
#[cfg(feature="diagnostics")]
pub(crate)mod exact_typing_probe{
 use super::*;use std::cell::Cell;
 pub(super)type Key=KEY_TYPE;
 thread_local!{static ACTIVE:Cell<bool>=const{Cell::new(false)};static COUNTS:Cell<[u64;16]>=const{Cell::new([0;16])};}
 fn count(i:usize){COUNTS.with(|c|{let mut x=c.get();x[i]+=1;c.set(x);});}
 pub(crate)struct Scope{active:bool,previous:bool}
 impl Scope{pub(crate)fn enter(active:bool)->Self{let previous=ACTIVE.with(|x|x.replace(active));if active{COUNTS.with(|x|x.set([0;16]));}Self{active,previous}}}
 impl Drop for Scope{fn drop(&mut self){if self.active{COUNTS.with(|x|eprintln!("EXACT_TYPING_REUSE_PROBE:counts={:?}",x.get()));}ACTIVE.with(|x|x.set(self.previous));}}
 pub(super)fn begin(c:&TypeChecker<'_>,term:&Closure,context:&[TypeValue],remaining:usize,depth:usize)->Option<(Key,bool)>{
  if !ACTIVE.with(Cell::get){return None;}count(0);
  if depth>=48||remaining<context.len()+4{return None;}
  if !matches!(c.expressions.get(term.expr),Some(Expr::App{..}|Expr::Proj{..}|Expr::Lam{..}|Expr::Pi{..}|Expr::Let{..}|Expr::LetNondep{..})){
   count(11);match c.expressions.get(term.expr){Some(Expr::Const{..})=>count(12),Some(Expr::BVar(_))=>count(13),Some(Expr::Sort(_))=>count(14),_=>count(15)}return None;
  }
  if context.len()>64{count(8);return None;}
  let mut scope=Vec::with_capacity(context.len());for ty in context{let TypeValue::Term(t)=ty else{count(9);return None;};PUSH_SCOPE}
  count(1);let key=MAKE_KEY;let kind=c.typing_reuse_probe.borrow().positive.get(&key).map(|r|r.2);
  if let Some(kind)=kind{count(2+kind);}else{count(5);}Some((key,kind.is_some()))
 }
 pub(super)fn finish(c:&TypeChecker<'_>,probe:Option<(Key,bool)>,term:&Closure,context:&[TypeValue],result:Option<&TypeValue>){
  let Some((key,hit))=probe else{return;};let Some(result)=result else{if hit{count(7);}return;};
  let mut table=c.typing_reuse_probe.borrow_mut();if table.positive.contains_key(&key){return;}
  if table.positive.len()>=8192{count(10);CAPACITY_ACTION}
  let scope=context.iter().map(|t|{let TypeValue::Term(t)=t else{unreachable!()};t.clone()}).collect();
  let kind=match result{TypeValue::Term(_)=>0,TypeValue::Pi{..}=>1,TypeValue::Sort(_)=>2};
  table.order.push_back(key.clone());table.positive.insert(key,(term.clone(),scope,kind));count(6);
 }
}
'''
 s+=template.replace('KEY_TYPE',key).replace('PUSH_SCOPE',push).replace('MAKE_KEY',make).replace('CAPACITY_ACTION',capacity);p.write_text(s)
 p=out/'src/checker.rs';s=p.read_text();needle='        let declaration = export.declarations[declaration_index].clone();';assert s.count(needle)==1
 s=s.replace(needle,needle+'''\n        #[cfg(feature="diagnostics")]\n        let _typing_probe_scope=crate::typecheck::exact_typing_probe::Scope::enter(matches!(&declaration,Declaration::Theorem{name,..}if *name==NameId(19346)));''');p.write_text(s)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',required=True);a=p.parse_args();prepare(a.source,a.out,a.mode)
