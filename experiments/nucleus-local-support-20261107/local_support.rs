//! Local-support observation, not a typing, universe, or transport certificate.
use std::collections::BTreeSet;
use crate::id::{ExprId,IdTable};
use crate::syntax::Expr;
use crate::value::{Closure,EnvBinding,EnvFrame,Neutral,NeutralHead};
#[derive(Debug)]pub(crate)struct Support{pub(crate)complete:bool,pub(crate)reason:&'static str,pub(crate)free:BTreeSet<(u64,u64)>,pub(crate)captures:BTreeSet<u64>,pub(crate)visits:usize}
impl Support{pub(crate)fn closed(&self)->bool{self.complete&&self.free.is_empty()}pub(crate)fn json(&self)->serde_json::Value{serde_json::json!({"complete":self.complete,"status":if !self.complete{"UNKNOWN"}else if self.closed(){"CLOSED_LOCAL"}else{"OPEN_LOCAL"},"reason":self.reason,"free_binding_occurrences":self.free,"capture_nodes":self.captures.iter().take(16).collect::<Vec<_>>(),"capture_count":self.captures.len(),"visits":self.visits,"boundary":"node IDs are immutable binding occurrences, not semantic binder identity; local free support only; constant bodies not unfolded; universes/typing/context transport not certified; incomplete support is UNKNOWN"})}}
pub(crate)fn analyze(expressions:&IdTable<ExprId,Expr>,root:&Closure,work:&mut usize)->Support{
 type Key=(ExprId,u64,u64);
 enum Task<'a>{Enter(ExprId,&'a EnvFrame,u64),Exit(Key)}
 let mut out=Support{complete:false,reason:"allowance",free:BTreeSet::new(),captures:BTreeSet::new(),visits:0};
 let mut pending=vec![Task::Enter(root.expr,&root.env,0)];let(mut active,mut done)=(BTreeSet::new(),BTreeSet::new());
 while let Some(task)=pending.pop(){if *work==0{return out;}*work-=1;match task{
  Task::Exit(key)=>{active.remove(&key);done.insert(key);},
  Task::Enter(expr,frame,depth)=>{
   out.visits+=1;let key=(expr,frame.id(),depth);if done.contains(&key){continue;}if !active.insert(key){out.reason="active_cycle";return out;}
   pending.push(Task::Exit(key));let Some(node)=expressions.get(expr)else{out.reason="missing_source";return out;};
   match node{
    Expr::BVar(index)=>{if *index<depth{continue;}let Some((node,binding))=frame.observed_binding(*index-depth,work)else{out.reason=if *work==0{"allowance"}else{"missing_capture"};return out;};out.captures.insert(node);if out.captures.len()>128{out.reason="capture_cap";return out;}
     match binding{
      EnvBinding::Closure(value)=>pending.push(Task::Enter(value.expr,&value.env,0)), // stored closure owns its lexical depth
      EnvBinding::Free(free)=>{out.free.insert((node,free.0));},
      EnvBinding::Neutral(Neutral{head:NeutralHead::Free(free),spine})if spine.is_empty()=>{out.free.insert((node,free.0));},
      EnvBinding::NatLit(_)=>{},
      EnvBinding::Neutral(_)=>{out.reason="unsupported_neutral";return out;}
     }if out.free.len()>64{out.reason="free_origin_cap";return out;}
    },
    Expr::App{fun,arg}=>{pending.push(Task::Enter(*arg,frame,depth));pending.push(Task::Enter(*fun,frame,depth));},
    Expr::Lam{domain,body}|Expr::Pi{domain,body}=>{let Some(next)=depth.checked_add(1)else{out.reason="depth_overflow";return out;};pending.push(Task::Enter(*body,frame,next));pending.push(Task::Enter(*domain,frame,depth));},
    Expr::Let{ty,value,body}|Expr::LetNondep{ty,value,body}=>{let Some(next)=depth.checked_add(1)else{out.reason="depth_overflow";return out;};pending.push(Task::Enter(*body,frame,next));pending.push(Task::Enter(*value,frame,depth));pending.push(Task::Enter(*ty,frame,depth));},
    Expr::Proj{structure,..}=>pending.push(Task::Enter(*structure,frame,depth)),
    Expr::NatLit(_)|Expr::StrLit(_)|Expr::Sort(_)|Expr::Const{..}=>{},
   }
  }
 }}out.complete=true;out.reason="complete";out
}
use std::cell::RefCell;
struct State{owner:String,stage:&'static str,events:u64,trials:u64,quota:usize,spent:usize,both_closed:u64,any_open:u64,unknown:u64,samples:Vec<serde_json::Value>}
thread_local!{static CURRENT:RefCell<Option<State>>=const{RefCell::new(None)};}
pub(crate)struct Scope{previous:Option<State>,active:bool}
impl Scope{pub(crate)fn enter(owner:String,stage:&'static str)->Self{match CURRENT.try_with(|s|s.replace(Some(State{owner,stage,events:0,trials:0,quota:262144,spent:0,both_closed:0,any_open:0,unknown:0,samples:Vec::new()}))){Ok(previous)=>Self{previous,active:true},Err(_)=>Self{previous:None,active:false}}}}
impl Drop for Scope{fn drop(&mut self){if !self.active{return;}let previous=self.previous.take();if let Ok(Some(s))=CURRENT.try_with(|slot|slot.replace(previous)){eprintln!("NUCLEUS_LOCAL_SUPPORT:{}",serde_json::json!({"owner":s.owner,"stage":s.stage,"events":s.events,"trials":s.trials,"spent":s.spent,"remaining_quota":s.quota,"both_closed_local":s.both_closed,"any_complete_open":s.any_open,"both_status_not_decided":s.unknown,"samples":s.samples,"acceptance_authority":false,"boundary":"same-key/full-context mismatch resident slot events; first8 then every8192th event <=128 trials,4096 shared units per source/result pair,262144 per owner/stage; first32 samples only; local support not typing/universe/transport certificate; no saved-work claim"}));}}}
#[inline]pub(crate)fn active()->bool{CURRENT.try_with(|s|s.borrow().is_some()).unwrap_or(false)}
pub(crate)fn observe(expressions:&IdTable<ExprId,Expr>,source:&Closure,result:&Closure,old:&[Closure],new:&[crate::typecheck::TypeValue]){
 let _=CURRENT.try_with(|slot|{let mut slot=slot.borrow_mut();let Some(s)=slot.as_mut()else{return;};s.events+=1;if s.trials>=128||s.quota==0||!(s.events<=8||s.events%8192==0){return;}s.trials+=1;let grant=s.quota.min(4096);let mut work=grant;
 let a=analyze(expressions,source,&mut work);let b=analyze(expressions,result,&mut work);let spent=grant-work;s.quota-=spent;s.spent+=spent;
 if a.closed()&&b.closed(){s.both_closed+=1;}else if(a.complete&&!a.free.is_empty())||(b.complete&&!b.free.is_empty()){s.any_open+=1;}else{s.unknown+=1;}
 if s.samples.len()<32{
  let ordinals=a.free.iter().chain(&b.free).map(|(_,free)|*free).collect::<BTreeSet<_>>();
  let mut dependencies=Vec::new();for free in ordinals.iter().take(64){let same=usize::try_from(*free).ok().and_then(|i|Some((old.get(i)?,new.get(i)?))).map(|(a,b)|matches!(b,crate::typecheck::TypeValue::Term(b)if(a.expr,a.env.id(),a.levels.identity())==(b.expr,b.env.id(),b.levels.identity())));dependencies.push(serde_json::json!({"free_ordinal":free,"exact_context_handle_at_observed_ordinal":same}));}
  s.samples.push(serde_json::json!({"event":s.events,"source":source.expr.0,"result":result.expr.0,"old_len":old.len(),"new_len":new.len(),"spent":spent,"source_support":a.json(),"result_support":b.json(),"observed_dependencies":dependencies,"dependency_ordinal_count":ordinals.len(),"dependencies_truncated":ordinals.len()>64,"dependency_boundary":"first64 union ordinals only; partial unless BOTH traversals complete and dependencies_truncated is false; no transitive context-domain support or typing-derivation dependency claim; ordinal handle match does not establish binder identity"}));
 }
 });
}
#[cfg(test)]mod tests{
 use super::*;use crate::value::{FreeId,LevelSubstitution};use crate::id::{LevelId,NameId};
 fn fixture()->IdTable<ExprId,Expr>{let mut e=IdTable::default();for(id,x)in[(0,Expr::Sort(LevelId(0))),(1,Expr::BVar(0)),(2,Expr::BVar(1)),(3,Expr::Const{name:NameId(1),levels:vec![]}),(4,Expr::Lam{domain:ExprId(0),body:ExprId(1)}),(5,Expr::Lam{domain:ExprId(0),body:ExprId(2)}),(6,Expr::App{fun:ExprId(3),arg:ExprId(1)}),(7,Expr::App{fun:ExprId(7),arg:ExprId(3)})]{e.insert(ExprId(id),x).unwrap();}e}
 fn t(id:u64,env:EnvFrame)->Closure{Closure::new(ExprId(id),env)}
 #[test]fn raw_alias_can_hide_closed_value(){let e=fixture();let x=t(1,EnvFrame::empty().extend(t(3,EnvFrame::empty())));let s=analyze(&e,&x,&mut 128);assert!(s.closed());assert_eq!(s.captures.len(),1);}
 #[test]fn virtual_local_does_not_become_ambient_support(){let e=fixture();let s=analyze(&e,&t(4,EnvFrame::empty()),&mut 128);assert!(s.closed());assert!(s.captures.is_empty());}
 #[test]fn captured_closure_resets_virtual_depth(){let e=fixture();let x=t(5,EnvFrame::empty().extend(t(1,EnvFrame::empty().extend_free(FreeId(0)))));let s=analyze(&e,&x,&mut 128);assert!(s.complete);assert_eq!(s.free.len(),1);assert!(!s.closed());}
 #[test]fn same_ordinal_distinct_binding_occurrences_stay_distinct(){let e=fixture();let a=analyze(&e,&t(1,EnvFrame::empty().extend_free(FreeId(0))),&mut 128);let b=analyze(&e,&t(1,EnvFrame::empty().extend_free(FreeId(0))),&mut 128);assert_eq!(a.free.iter().next().unwrap().1,b.free.iter().next().unwrap().1);assert_ne!(a.free,b.free);}
 #[test]fn same_origin_is_retained_through_different_alias_paths(){let e=fixture();let leaf=t(1,EnvFrame::empty().extend_free(FreeId(4)));let a=analyze(&e,&leaf,&mut 128);let b=analyze(&e,&t(1,EnvFrame::empty().extend(leaf)),&mut 128);assert_eq!(a.free,b.free);}
 #[test]fn active_cycle_missing_capture_and_no_work_remain_unknown(){let e=fixture();for(x,n)in[(t(7,EnvFrame::empty()),128),(t(1,EnvFrame::empty()),128),(t(3,EnvFrame::empty()),0)]{let s=analyze(&e,&x,&mut {n});assert!(!s.complete);assert!(!s.closed());}}
 #[test]fn completed_shared_child_is_not_an_active_cycle(){let mut e=fixture();e.insert(ExprId(8),Expr::App{fun:ExprId(3),arg:ExprId(3)}).unwrap();assert!(analyze(&e,&t(8,EnvFrame::empty()),&mut 128).closed());}
 #[test]fn projection_and_let_follow_all_source_children(){let mut e=fixture();e.insert(ExprId(8),Expr::Proj{type_name:NameId(1),index:0,structure:ExprId(1)}).unwrap();e.insert(ExprId(9),Expr::Let{ty:ExprId(0),value:ExprId(1),body:ExprId(1)}).unwrap();for id in [8,9]{let s=analyze(&e,&t(id,EnvFrame::empty().extend_free(FreeId(2))),&mut 128);assert!(s.complete&&!s.closed());}}
 #[test]fn unsupported_neutral_never_claims_closed(){let e=fixture();let x=t(1,EnvFrame::empty().extend_neutral(Neutral{head:NeutralHead::Free(FreeId(1)),spine:vec![t(3,EnvFrame::empty())]}));assert!(!analyze(&e,&x,&mut 128).complete);}
 #[test]fn captures_are_borrowed_and_meters_are_local(){let e=fixture();let frame=EnvFrame::empty().extend(t(3,EnvFrame::empty()));let x=Closure::with_levels(ExprId(1),frame.clone(),LevelSubstitution::default());let owners=frame.strong_owners();let mut work=128;assert!(analyze(&e,&x,&mut work).closed());assert!(work<128);assert_eq!(frame.strong_owners(),owners);}
}

#[cfg(test)]mod budget_controls{
 use super::*;use crate::id::NameId;
 fn fixture()->(IdTable<ExprId,Expr>,Closure){let mut e=IdTable::default();e.insert(ExprId(0),Expr::Const{name:NameId(1),levels:vec![]}).unwrap();(e,Closure::new(ExprId(0),EnvFrame::empty()))}
 #[test]fn source_and_result_share_one_allowance_and_partial_result_is_unknown(){let(e,t)=fixture();let mut work=3;assert!(analyze(&e,&t,&mut work).closed());assert_eq!(work,1);let b=analyze(&e,&t,&mut work);assert!(!b.complete&&!b.closed());assert_eq!(work,0);}
 #[test]fn paid_parent_lookup_returns_actual_node_without_cloning_payload(){let leaf=EnvFrame::empty().extend_free(crate::value::FreeId(7));let node=leaf.id();let frame=leaf.extend_free(crate::value::FreeId(8));let mut zero=0;assert!(frame.observed_binding(1,&mut zero).is_none());let mut one=1;assert!(frame.observed_binding(1,&mut one).is_none());let mut two=2;let(id,value)=frame.observed_binding(1,&mut two).unwrap();assert_eq!(id,node);assert!(matches!(value,EnvBinding::Free(crate::value::FreeId(7))));assert_eq!(two,0);}
 #[test]fn owner_quota_exhaustion_prevents_later_support_work(){let(e,t)=fixture();let _scope=Scope::enter("quota".into(),"test");CURRENT.with(|s|s.borrow_mut().as_mut().unwrap().quota=3);observe(&e,&t,&t,&[],&[]);observe(&e,&t,&t,&[],&[]);CURRENT.with(|s|{let slot=s.borrow();let s=slot.as_ref().unwrap();assert_eq!(s.events,2);assert_eq!(s.trials,1);assert_eq!(s.spent,3);assert_eq!(s.quota,0);assert_eq!(s.both_closed,0);assert_eq!(s.unknown,1);});}
}
