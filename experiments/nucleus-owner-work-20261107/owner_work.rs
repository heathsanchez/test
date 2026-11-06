//! Read-only, bounded census. No observation is a type or equality premise.
use std::{cell::RefCell,collections::{HashMap,HashSet}};
use serde_json::{json,Value};
const CAP:usize=8192;const BYTE_CAP:usize=8*1024*1024;const KEY_CAP:usize=8192;
#[derive(Default)]struct Row{calls:u64,completed:u64,declined:u64,debits:u64,completed_before:u64,completed_before_debits:u64}
#[derive(Default)]struct Family{calls:u64,envs:HashSet<u64>,envs_truncated:bool}
#[derive(Default)]struct Census{owner:String,stage:String,rows:HashMap<String,Row>,families:HashMap<(u64,usize),Family>,bytes:usize,calls:u64,unkeyed:u64,capacity_drops:u64,nesting:usize,max_nesting:usize,root_calls:u64,root_debits:u64,zero_debit_declines:u64}
pub(crate) struct Ticket{key:Option<String>,start:usize,root:bool,completed_before:bool}
impl Census{
 fn begin(&mut self,key:Option<String>,expr:u64,env:u64,ctx:usize,start:usize)->Ticket{
  self.calls+=1;self.nesting+=1;self.max_nesting=self.max_nesting.max(self.nesting);
  if self.families.len()<1024||self.families.contains_key(&(expr,ctx)) {let f=self.families.entry((expr,ctx)).or_default();f.calls+=1;if f.envs.len()<64{f.envs.insert(env);}else if !f.envs.contains(&env){f.envs_truncated=true;}}
  let key=key.filter(|k|k.len()<=KEY_CAP);
  let key=if let Some(k)=key{if self.rows.contains_key(&k){Some(k)}else if self.rows.len()<CAP&&self.bytes+k.len()<=BYTE_CAP{self.bytes+=k.len();self.rows.insert(k.clone(),Row::default());Some(k)}else{self.capacity_drops+=1;None}}else{self.unkeyed+=1;None};
  let completed_before=key.as_ref().is_some_and(|k|self.rows[k].completed>0);
  Ticket{key,start,root:self.nesting==1,completed_before}
 }
 fn finish(&mut self,t:Ticket,end:usize,completed:bool){
  self.nesting=self.nesting.saturating_sub(1);let debit=t.start.saturating_sub(end)as u64;
  if t.root{self.root_calls+=1;self.root_debits+=debit;}
  if !completed&&end==0{self.zero_debit_declines+=1;}
  if let Some(k)=t.key{let r=self.rows.get_mut(&k).unwrap();r.calls+=1;r.debits+=debit;if completed{r.completed+=1}else{r.declined+=1};if t.completed_before{r.completed_before+=1;r.completed_before_debits+=debit;}}
 }
 fn report(&self)->Value{
  let mut rows=self.rows.iter().collect::<Vec<_>>();rows.sort_by(|a,b|b.1.debits.cmp(&a.1.debits).then_with(||a.0.cmp(b.0)));
  let mut families=self.families.iter().collect::<Vec<_>>();families.sort_by(|a,b|b.1.calls.cmp(&a.1.calls).then_with(||a.0.cmp(b.0)));
  json!({"schema":"nucleus.owner_work.v1","diagnostic_only":true,"acceptance_authority":false,"owner":self.owner,"stage":self.stage,"calls":self.calls,"keyed_unique":self.rows.len(),"unkeyed":self.unkeyed,"capacity_drops":self.capacity_drops,"key_bytes":self.bytes,"root_calls":self.root_calls,"root_local_debits":self.root_debits,"max_nesting":self.max_nesting,"declines_at_zero_remaining":self.zero_debit_declines,"completed_before_query_calls":self.rows.values().map(|r|r.completed_before).sum::<u64>(),"completed_before_query_inclusive_debits":self.rows.values().map(|r|r.completed_before_debits).sum::<u64>(),"repeated_exact_calls":self.rows.values().map(|r|r.calls.saturating_sub(1)).sum::<u64>(),"limits":{"rows":CAP,"bytes":BYTE_CAP,"key_bytes":KEY_CAP,"context":64,"depth":48,"families":1024,"envs_per_family":64},"cost_boundary":"Local remaining-counter decrements only. Nested row debits overlap; not global owner work, time or a realizable saving. Metadata cost excluded.","scope_boundary":"Exact keys retain authority, source, immutable env, actual universes, full bounded context, strictness, policy, flags and epoch. Expr/context-width families do NOT prove capture or scope equivalence.","top_exact":rows.iter().take(24).map(|(k,r)|json!({"key":k.chars().take(512).collect::<String>(),"key_display_truncated":k.len()>512,"calls":r.calls,"completed":r.completed,"declined":r.declined,"inclusive_debits":r.debits,"completed_before_calls":r.completed_before,"completed_before_inclusive_debits":r.completed_before_debits})).collect::<Vec<_>>(),"top_families":families.iter().take(24).map(|((e,c),f)|json!({"expr":e,"context_width":c,"calls":f.calls,"distinct_env_ids":f.envs.len(),"envs_truncated":f.envs_truncated})).collect::<Vec<_>>()})
 }
}
thread_local!{static ACTIVE:RefCell<Option<Census>>=const{RefCell::new(None)};}
pub(crate) struct Scope(Option<Census>);
impl Scope{pub(crate) fn enter(owner:&str,stage:&str)->Option<Self>{
 if std::env::var("NUCLEUS_DIAGNOSTIC_WORK_OWNER").ok().as_deref()!=Some(owner)||!stage.ends_with(".value"){return None;}
 let old=ACTIVE.with(|s|s.replace(Some(Census{owner:owner.into(),stage:stage.into(),..Census::default()})));Some(Self(old))
}}
impl Drop for Scope{fn drop(&mut self){let result=ACTIVE.with(|s|s.replace(self.0.take()));if let Some(c)=result{eprintln!("NUCLEUS_OWNER_WORK:{}",c.report());}}}
pub(crate) fn active()->bool{ACTIVE.with(|s|s.borrow().is_some())}
pub(crate) fn begin(key:Option<String>,expr:u64,env:u64,ctx:usize,start:usize)->Option<Ticket>{ACTIVE.with(|s|s.borrow_mut().as_mut().map(|c|c.begin(key,expr,env,ctx,start)))}
pub(crate) fn finish(t:Option<Ticket>,end:usize,completed:bool){if let Some(t)=t{ACTIVE.with(|s|{if let Some(c)=s.borrow_mut().as_mut(){c.finish(t,end,completed)}})}}
#[cfg(test)]mod tests{use super::*;
 #[test]fn matches_are_observed_before_results_and_scope_keys_do_not_merge(){let mut c=Census::default();let t=c.begin(Some("a".into()),1,0,0,10);c.finish(t,5,true);let t=c.begin(Some("b".into()),1,1,0,10);c.finish(t,0,false);let t=c.begin(Some("a".into()),1,0,0,10);c.finish(t,9,true);let r=c.report();assert_eq!(r["calls"],3);assert_eq!(r["keyed_unique"],2);assert_eq!(r["completed_before_query_calls"],1);assert_eq!(r["completed_before_query_inclusive_debits"],1);assert_eq!(r["declines_at_zero_remaining"],1);}
 #[test]fn truncation_and_capacity_are_visible_and_do_not_invent_matches(){let mut c=Census::default();let t=c.begin(Some("a".repeat(KEY_CAP+1)),1,0,0,2);c.finish(t,0,false);c.bytes=BYTE_CAP;let t=c.begin(Some("new".into()),2,0,0,1);c.finish(t,0,false);let r=c.report();assert_eq!(r["unkeyed"],1);assert_eq!(r["capacity_drops"],1);assert_eq!(r["completed_before_query_calls"],0);}
 #[test]fn root_debits_do_not_sum_nested_inclusive_debits(){let mut c=Census::default();let a=c.begin(Some("a".into()),1,0,0,10);let b=c.begin(Some("b".into()),2,0,0,8);c.finish(b,5,true);c.finish(a,2,false);let r=c.report();assert_eq!(r["root_calls"],1);assert_eq!(r["root_local_debits"],8);assert_eq!(r["max_nesting"],2);assert_eq!(r["acceptance_authority"],false);}
}
