#[derive(Clone,Default,Debug)]struct ContextSpine(Option<Rc<ContextNode>>);
#[derive(Debug)]struct ContextNode{parent:ContextSpine,value:TypeValue,len:usize}
impl ContextSpine{
 fn len(&self)->usize{self.0.as_ref().map_or(0,|n|n.len)}
 fn push(&self,value:TypeValue)->Self{Self(Some(Rc::new(ContextNode{parent:self.clone(),value,len:self.len()+1})))}
 fn ancestor(&self,n:usize)->Self{let mut p=self.clone();while p.len()>n{p=p.0.as_ref().unwrap().parent.clone();}p}
 fn equals_slice(&self,s:&[TypeValue])->bool{if self.len()!=s.len(){return false;}let mut p=self;for value in s.iter().rev(){let n=p.0.as_ref().unwrap();if n.value!=*value{return false;}p=&n.parent;}true}
 fn starts_with(&self,s:&[TypeValue])->bool{self.len()>=s.len()&&self.ancestor(s.len()).equals_slice(s)}
 fn is_prefix_of(&self,s:&[TypeValue])->bool{self.len()<=s.len()&&self.equals_slice(&s[..self.len()])}
 fn to_vec(&self)->Vec<TypeValue>{let mut v=Vec::with_capacity(self.len());let mut p=self;while let Some(n)=&p.0{v.push(n.value.clone());p=&n.parent;}v.reverse();v}
}
impl PartialEq for ContextSpine{fn eq(&self,o:&Self)->bool{if self.len()!=o.len(){return false;}let(mut a,mut b)=(self,o);loop{match(&a.0,&b.0){(None,None)=>return true,(Some(x),Some(y))=>{if Rc::ptr_eq(x,y){return true;}if x.value!=y.value{return false;}a=&x.parent;b=&y.parent;},_=>return false}}}}
impl Eq for ContextSpine{}
impl PartialEq<&[TypeValue]> for ContextSpine{fn eq(&self,s:&&[TypeValue])->bool{self.equals_slice(s)}}
#[derive(Default)]struct ContextArena{last:ContextSpine}
impl ContextArena{
 fn capture(&mut self,s:&[TypeValue])->ContextSpine{
  let same=self.last.ancestor(s.len());if same.equals_slice(s){self.last=same.clone();return same;}
  if !s.is_empty(){let parent=self.last.ancestor(s.len()-1);if parent.equals_slice(&s[..s.len()-1]){self.last=parent.push(s.last().unwrap().clone());return self.last.clone();}}
  let mut p=ContextSpine::default();for t in s{p=p.push(t.clone());}self.last=p.clone();p
 }
}
#[cfg(test)]mod context_spine_tests{
 use super::*;
 #[test]fn prefixes_and_sibling_forks_preserve_exact_vector_contents(){
  let mut arena=ContextArena::default();let mut values=Vec::new();let mut saved=Vec::new();
  for i in 0..200{values.push(TypeValue::Sort(LevelTerm::param(format!("u{i}"))));let p=arena.capture(&values);assert_eq!(p.to_vec(),values);assert!(p.equals_slice(&values));saved.push(p);}
  for (i,p) in saved.iter().enumerate(){assert_eq!(p.len(),i+1);assert!(p.is_prefix_of(&values));for j in 0..=i{assert!(p.starts_with(&values[..j]));}let mut wrong=values[..i+1].to_vec();wrong[i]=TypeValue::Sort(LevelTerm::Zero);assert!(!p.equals_slice(&wrong));}
  let mut a=values[..100].to_vec();a.push(TypeValue::Sort(LevelTerm::param("a")));let left=arena.capture(&a);
  let mut b=values[..100].to_vec();b.push(TypeValue::Sort(LevelTerm::param("b")));let right=arena.capture(&b);assert_ne!(left,right);assert_eq!(left.to_vec(),a);assert_eq!(right.to_vec(),b);assert!(left.starts_with(&values[..100]));
 }
}
