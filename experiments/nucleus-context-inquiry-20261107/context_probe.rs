//! Bounded diagnostic observation. Never supplies facts, results, or semantic fuel.
use std::cell::RefCell;
use crate::value::Closure;
use crate::typecheck::TypeValue;
const LIMIT:usize=64;
const NAMES:[&str;21]=["same_key_context_mismatch","same_length","old_exact_prefix","new_exact_prefix","unequal_length_nonprefix","changed_expr","changed_env","changed_levels","result_term","result_pi","result_sort","inquiry_selected","inquiry_unselected","inquiry_quota_empty","same_length_relational_established","prefix_relational_established","relational_not_established","relational_failed_at_zero_balance","inquiry_work_spent","common_entries_examined","unsupported_context"];
struct State{owner:String,stage:&'static str,counts:[u64;21],quota:usize,trials:usize,samples:Vec<serde_json::Value>}
thread_local!{static CURRENT:RefCell<Option<State>>=const{RefCell::new(None)};}
pub(crate)struct Scope{previous:Option<State>,active:bool}
impl Scope{pub(crate)fn enter(owner:String,stage:&'static str)->Self{match CURRENT.try_with(|s|s.replace(Some(State{owner,stage,counts:[0;21],quota:262144,trials:0,samples:Vec::new()}))){Ok(previous)=>Self{previous,active:true},Err(_)=>Self{previous:None,active:false}}}}
impl Drop for Scope{fn drop(&mut self){if !self.active{return;}let previous=self.previous.take();if let Ok(Some(s))=CURRENT.try_with(|slot|slot.replace(previous)){let counts=NAMES.iter().zip(s.counts).collect::<std::collections::BTreeMap<_,_>>();eprintln!("NUCLEUS_CONTEXT_PROBE:{}",serde_json::json!({"owner":s.owner,"stage":s.stage,"counts":counts,"remaining_inquiry_quota":s.quota,"trials":s.trials,"samples":s.samples,"acceptance_authority":false,"boundary":"same complete-key resident slot mismatches; overlapping events, not distinct requests or savings; <=64 common entries per event; first16 then every4096th event, <=128 trials, <=4096 steps per trial, <=262144 inquiry steps per owner/stage; samples first32 selected; false comparison is UNKNOWN (including unaffordable operations with positive balance); prefix compatibility is not whole-context equivalence"}));}}}
#[inline]pub(crate)fn active()->bool{CURRENT.try_with(|s|s.borrow().is_some()).unwrap_or(false)}
fn id(t:&Closure)->(u64,u64,usize){(t.expr.0,t.env.id(),t.levels.identity())}
#[derive(Debug,PartialEq)]
pub(crate)struct Shape{pub(crate)category:usize,pub(crate)expr:bool,pub(crate)env:bool,pub(crate)levels:bool,pub(crate)common:usize}
pub(crate)fn classify(old:&[Closure],new:&[TypeValue])->Option<Shape>{
 if old.len()>LIMIT||new.len()>LIMIT{return None;}
 let(mut expr,mut env,mut levels)=(false,false,false);
 for(a,b)in old.iter().zip(new){let TypeValue::Term(b)=b else{return None;};expr|=a.expr!=b.expr;env|=a.env.id()!=b.env.id();levels|=a.levels.identity()!=b.levels.identity();}
 // Inspect unmatched suffix too: no unbounded scan or non-Term assumption.
 if new.iter().any(|v|!matches!(v,TypeValue::Term(_))){return None;}
 let identical=!(expr||env||levels);
 let category=if old.len()==new.len(){1}else if identical&&old.len()<new.len(){2}else if identical{3}else{4};
 Some(Shape{category,expr,env,levels,common:old.len().min(new.len())})
}
pub(crate)fn observe(source:u64,old:&[Closure],new:&[TypeValue],result:&TypeValue,mut compare:impl FnMut(&Closure,&Closure,&mut usize)->bool){
 let _=CURRENT.try_with(|slot|{let mut slot=slot.borrow_mut();let Some(s)=slot.as_mut()else{return;};s.counts[0]+=1;
 let Some(shape)=classify(old,new)else{s.counts[20]+=1;return;};s.counts[shape.category]+=1;s.counts[5]+=u64::from(shape.expr);s.counts[6]+=u64::from(shape.env);s.counts[7]+=u64::from(shape.levels);s.counts[19]+=shape.common as u64;
 let kind=match result{TypeValue::Term(_)=>8,TypeValue::Pi{..}=>9,TypeValue::Sort(_)=>10};s.counts[kind]+=1;
 let n=s.counts[0];if !(n<=16||n%4096==0)||s.trials>=128{s.counts[12]+=1;return;}if s.quota==0{s.counts[13]+=1;return;}
 s.counts[11]+=1;s.trials+=1;let grant=s.quota.min(4096);let mut work=grant;let mut established=true;let mut failed_at=None;
 for(i,(a,b))in old.iter().zip(new).enumerate(){let TypeValue::Term(b)=b else{unreachable!()};if work==0{established=false;failed_at=Some(i);break;}work-=1;if id(a)!=id(b)&&!compare(a,b,&mut work){established=false;failed_at=Some(i);break;}}
 let spent=grant-work;s.quota-=spent;s.counts[18]+=spent as u64;
 if established{s.counts[if shape.category==1{14}else{15}]+=1;}else{s.counts[16]+=1;if work==0{s.counts[17]+=1;}}
 if s.samples.len()<32{let changed=old.iter().zip(new).enumerate().filter_map(|(i,(a,b))|{let TypeValue::Term(b)=b else{return None;};(id(a)!=id(b)).then(||serde_json::json!({"index":i,"old":id(a),"new":id(b)}))}).take(4).collect::<Vec<_>>();s.samples.push(serde_json::json!({"event":n,"source":source,"old_len":old.len(),"new_len":new.len(),"shape":shape.category,"result_kind":NAMES[kind],"common_prefix_relation_established":established,"whole_context_relation_established":established&&shape.category==1,"spent":spent,"failed_at":failed_at,"changed":changed}));}
 });
}
#[cfg(test)]mod tests{
 use super::*;use crate::id::ExprId;use crate::value::{EnvFrame,FreeId};use crate::level::LevelTerm;
 fn t(id:u64)->Closure{Closure::new(ExprId(id),EnvFrame::empty())}
 #[test]fn identity_prefix_and_changed_prefix_are_separate(){let a=t(1);let b=t(2);let old=vec![a.clone()];let new=vec![TypeValue::Term(a.clone()),TypeValue::Term(b.clone())];assert_eq!(classify(&old,&new).unwrap().category,2);let long=vec![a.clone(),b.clone()];assert_eq!(classify(&long,&[TypeValue::Term(a.clone())]).unwrap().category,3);assert_eq!(classify(&old,&[TypeValue::Term(b)]).unwrap().category,1);assert_eq!(classify(&old,&[TypeValue::Term(t(2)),TypeValue::Term(t(3))]).unwrap().category,4);}
 #[test]fn nonterm_suffix_and_long_context_are_explicitly_unsupported(){assert!(classify(&[],&[TypeValue::Sort(LevelTerm::Zero)]).is_none());assert!(classify(&vec![t(1);65],&[]).is_none());}
 #[test]fn changed_captured_values_are_not_identity_prefixes(){let a=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(1)));let b=Closure::new(ExprId(1),EnvFrame::empty().extend_free(FreeId(2)));let s=classify(&[a],&[TypeValue::Term(b)]).unwrap();assert!(s.env);assert!(!s.expr);assert_eq!(s.category,1);}
 #[test]fn false_inquiry_never_becomes_equivalence_and_quota_is_separate(){let _scope=Scope::enter("test".into(),"test");let a=t(1);let b=t(2);observe(3,&[a],&[TypeValue::Term(b)],&TypeValue::Sort(LevelTerm::Zero),|_,_,work|{*work-=7;false});CURRENT.with(|s|{let slot=s.borrow();let s=slot.as_ref().unwrap();assert_eq!(s.counts[14],0);assert_eq!(s.counts[16],1);assert_eq!(s.quota,262144-8);assert_eq!(s.samples[0]["whole_context_relation_established"],false);});}
 #[test]fn inactive_observation_never_invokes_comparer(){assert!(!active());observe(0,&[t(1)],&[TypeValue::Term(t(2))],&TypeValue::Sort(LevelTerm::Zero),|_,_,_|panic!("inactive comparer"));}
 #[test]fn owner_quota_caps_all_trials_and_samples(){let _scope=Scope::enter("quota".into(),"test");for _ in 0..4097{observe(0,&[t(1)],&[TypeValue::Term(t(2))],&TypeValue::Sort(LevelTerm::Zero),|_,_,work|{*work=0;false});}CURRENT.with(|s|{let slot=s.borrow();let s=slot.as_ref().unwrap();assert_eq!(s.trials,17);assert_eq!(s.quota,262144-17*4096);assert!(s.samples.len()<=32);});}
}
#[cfg(test)]pub(crate)fn test_counts()->[u64;21]{CURRENT.with(|s|s.borrow().as_ref().unwrap().counts)}

#[cfg(test)]mod additional_controls{
 use super::*;use crate::id::ExprId;use crate::value::EnvFrame;use crate::level::LevelTerm;
 fn t(n:u64)->Closure{Closure::new(ExprId(n),EnvFrame::empty())}
 #[test]fn established_overlap_of_unequal_contexts_never_claims_whole_equivalence(){let _scope=Scope::enter("prefix".into(),"test");observe(5,&[t(1)],&[TypeValue::Term(t(2)),TypeValue::Term(t(3))],&TypeValue::Sort(LevelTerm::Zero),|_,_,_|true);CURRENT.with(|s|{let slot=s.borrow();let s=slot.as_ref().unwrap();assert_eq!(s.counts[15],1);assert_eq!(s.counts[14],0);assert_eq!(s.samples[0]["whole_context_relation_established"],false);});}
 #[test]fn depleted_quota_prevents_later_comparer_calls(){let _scope=Scope::enter("quota".into(),"test");CURRENT.with(|s|s.borrow_mut().as_mut().unwrap().quota=3);observe(5,&[t(1)],&[TypeValue::Term(t(2))],&TypeValue::Sort(LevelTerm::Zero),|_,_,w|{assert_eq!(*w,2);*w=0;false});observe(5,&[t(1)],&[TypeValue::Term(t(2))],&TypeValue::Sort(LevelTerm::Zero),|_,_,_|panic!("quota exceeded"));CURRENT.with(|s|{let slot=s.borrow();let s=slot.as_ref().unwrap();assert_eq!(s.quota,0);assert_eq!(s.trials,1);assert_eq!(s.counts[13],1);});}
}
