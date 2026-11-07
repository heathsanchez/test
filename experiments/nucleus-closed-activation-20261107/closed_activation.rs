//! Bounded attribution only; never authorizes semantic reuse or spends checker fuel.
use std::cell::RefCell;
struct State{owner:String,stage:&'static str,misses:u64,hits:u64,chosen:u64,trials:u64,samples:Vec<serde_json::Value>}
thread_local!{static CURRENT:RefCell<Option<State>>=const{RefCell::new(None)};}
pub(crate)struct Scope{previous:Option<State>,active:bool}
impl Scope{pub(crate)fn enter(owner:String,stage:&'static str)->Self{match CURRENT.try_with(|s|s.replace(Some(State{owner,stage,misses:0,hits:0,chosen:0,trials:0,samples:Vec::new()}))){Ok(previous)=>Self{previous,active:true},Err(_)=>Self{previous:None,active:false}}}}
impl Drop for Scope{fn drop(&mut self){if !self.active{return;}let previous=self.previous.take();if let Ok(Some(s))=CURRENT.try_with(|slot|slot.replace(previous)){eprintln!("NUCLEUS_CLOSED_ACTIVATION:{}",serde_json::json!({"owner":s.owner,"stage":s.stage,"uncached_requests":s.misses,"closed_replay_hits":s.hits,"canonical_chosen":s.chosen,"trials":s.trials,"samples":s.samples,"acceptance_authority":false,"boundary":"same candidate code, read-only attribution; misses overlap nested calls, no savings estimate; first16 then every8192nd miss <=128 samples; structural check uses independent32 units, not semantic fuel; samples retain first32"}));}}}
#[inline]pub(crate)fn active()->bool{CURRENT.try_with(|s|s.borrow().is_some()).unwrap_or(false)}
pub(crate)fn hit(){let _=CURRENT.try_with(|slot|{if let Some(s)=slot.borrow_mut().as_mut(){s.hits+=1;}});}
pub(crate)fn observe(chosen:bool,view:impl FnOnce()->serde_json::Value){let _=CURRENT.try_with(|slot|{let mut slot=slot.borrow_mut();let Some(s)=slot.as_mut()else{return;};s.misses+=1;s.chosen+=u64::from(chosen);if s.trials>=128||!(s.misses<=16||s.misses%8192==0){return;}s.trials+=1;let v=view();if s.samples.len()<32{s.samples.push(v);}});}
