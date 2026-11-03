// Structural fingerprints accelerate hashing, never decide equality by themselves.
#[derive(Clone,Debug)]
pub struct SharedType(Rc<SharedTypeNode>);
#[derive(Debug)]
struct SharedTypeNode{value:TypeValue,fingerprint:u64}
impl SharedType{
 pub fn new(value:TypeValue)->Self{
  let mut h=std::collections::hash_map::DefaultHasher::new();
  std::hash::Hash::hash(&value,&mut h);
  let fingerprint=std::hash::Hasher::finish(&h);
  Self(Rc::new(SharedTypeNode{value,fingerprint}))
 }
}
impl std::ops::Deref for SharedType{type Target=TypeValue;fn deref(&self)->&TypeValue{&self.0.value}}
impl AsRef<TypeValue> for SharedType{fn as_ref(&self)->&TypeValue{&self.0.value}}
impl PartialEq for SharedType{fn eq(&self,other:&Self)->bool{Rc::ptr_eq(&self.0,&other.0)||(self.0.fingerprint==other.0.fingerprint&&self.0.value==other.0.value)}}
impl Eq for SharedType{}
impl std::hash::Hash for SharedType{fn hash<H:std::hash::Hasher>(&self,h:&mut H){std::hash::Hash::hash(&self.0.fingerprint,h)}}
#[cfg(test)]mod shared_type_tests{
 use super::*;
 #[test]fn hash_collision_cannot_establish_equality(){
  let a=SharedType(Rc::new(SharedTypeNode{value:TypeValue::Sort(LevelTerm::Zero),fingerprint:7}));
  let b=SharedType(Rc::new(SharedTypeNode{value:TypeValue::Sort(LevelTerm::param("u")),fingerprint:7}));assert_ne!(a,b);
 }
 #[test]fn independently_allocated_equal_nodes_have_equal_hashes(){
  use std::hash::{Hash,Hasher};
  let a=SharedType::new(TypeValue::Sort(LevelTerm::Zero));let b=SharedType::new(TypeValue::Sort(LevelTerm::Zero));assert_eq!(a,b);
  let hash=|x:&SharedType|{let mut h=std::collections::hash_map::DefaultHasher::new();x.hash(&mut h);h.finish()};assert_eq!(hash(&a),hash(&b));assert_eq!(hash(&a),hash(&a.clone()));
 }
}
