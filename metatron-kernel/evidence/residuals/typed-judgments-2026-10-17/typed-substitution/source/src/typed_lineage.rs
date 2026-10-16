//! Dependency-preserving storage for original checked binder witnesses.
//! Derived substitution witnesses are quarantined if any observed premise changes.
use std::cell::{RefCell,Ref,RefMut};
use std::collections::HashMap;
use std::ops::Deref;
use std::rc::Rc;
use super::TypeValue;
use super::CheckedBinderWitness;
use crate::value::EnvFrame;
type Entries=HashMap<u64,Option<CheckedBinderWitness>>;
pub(super) type Observation=(EnvFrame,Option<Option<CheckedBinderWitness>>);
pub(super) struct CheckedLineage {
 entries:RefCell<Entries>,
 dependencies:RefCell<HashMap<u64,Vec<Observation>>>,
 contexts:RefCell<HashMap<u64,(EnvFrame,Rc<Vec<TypeValue>>)>>,
}
impl CheckedLineage {
 pub(super) fn new(entries:Entries)->Self{Self{entries:RefCell::new(entries),dependencies:RefCell::new(HashMap::new()),contexts:RefCell::new(HashMap::new())}}
 pub(super) fn borrow(&self)->Ref<'_,Entries>{self.entries.borrow()}
 pub(super) fn borrow_mut(&self)->LineageMutation<'_>{LineageMutation{entries:self.entries.borrow_mut(),dependencies:&self.dependencies}}
 pub(super) fn derive(&self,node:u64,observations:Vec<Observation>,frame:EnvFrame,context:Rc<Vec<TypeValue>>){self.dependencies.borrow_mut().insert(node,observations);self.contexts.borrow_mut().insert(node,(frame,context));}
 pub(super) fn source_context(&self,node:u64)->Option<(EnvFrame,Rc<Vec<TypeValue>>)>{self.contexts.borrow().get(&node).cloned()}
 pub(super) fn cloned(&self)->Self{Self{entries:RefCell::new(self.entries.borrow().clone()),dependencies:RefCell::new(self.dependencies.borrow().clone()),contexts:RefCell::new(self.contexts.borrow().clone())}}

}
pub(super) struct LineageMutation<'a>{entries:RefMut<'a,Entries>,dependencies:&'a RefCell<HashMap<u64,Vec<Observation>>>}
impl Deref for LineageMutation<'_>{type Target=Entries;fn deref(&self)->&Entries{&self.entries}}
impl LineageMutation<'_>{
 pub(super) fn insert(&mut self,node:u64,witness:Option<CheckedBinderWitness>)->Option<Option<CheckedBinderWitness>>{let old=self.entries.insert(node,witness);self.propagate();old}
 pub(super) fn remove(&mut self,node:&u64)->Option<Option<CheckedBinderWitness>>{let old=self.entries.remove(node);self.propagate();old}
 fn propagate(&mut self){
  let dependencies=self.dependencies.borrow();
  // Each derived node depends only on earlier immutable frame identities.
  // Fixed-point propagation also handles later revocation of a derived premise.
  loop {
   let mut changed=false;
   for (node,premises) in dependencies.iter(){
    if !matches!(self.entries.get(node),Some(Some(_))){continue;}
    if premises.iter().any(|(frame,observed)|self.entries.get(&frame.id()).cloned()!=*observed){self.entries.insert(*node,None);changed=true;}
   }
   if !changed{break;}
  }
 }
}
