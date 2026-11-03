import difflib
from pathlib import Path

def conversion_patch(s,early=False,shared=False):
    def once(old,new):
        nonlocal s
        assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
    if early:
        once('    let mut remaining = budget;\n    let mut work =', '    if left == right {return Judgment::proven((), "guarded-relational-conversion");}\n    let mut remaining = budget;\n    let mut work =')
    if shared:
        s='use std::rc::Rc;\n'+s
        assert s.count('work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>')==4
        s=s.replace('work: &mut Vec<(TypeValue, TypeValue, usize, Vec<TypeValue>)>','work: &mut Vec<(TypeValue, TypeValue, usize, Rc<Vec<TypeValue>>)>')
        for fn in ['evaluated_free_eta','certified_structure_eta','compare_values','compare_nat_literal_neutral']:
            a=s.index('fn '+fn+'(');b=s.index(') ->',a)
            header=s[a:b];assert header.count('context: &[TypeValue]')==1
            s=s[:a]+header.replace('context: &[TypeValue]','context: &Rc<Vec<TypeValue>>')+s[b:]
        once('let context = local_context.as_slice();','let context = &local_context;')
        s=s.replace('context.to_vec()','Rc::clone(context)')
        once('initial_depth, Rc::clone(context))','initial_depth, Rc::new(context.to_vec()))')
        s=s.replace('body_context.push((*left_domain).clone());','Rc::make_mut(&mut body_context).push((*left_domain).clone());').replace('body_context.push(left_domain_type);','Rc::make_mut(&mut body_context).push(left_domain_type);')
        # Existing private-helper tests supply an explicit snapshot too.
        s=s.replace(',256,0,&[],&mut vec![],&mut HashMap::new())',',256,0,&Rc::new(vec![]),&mut vec![],&mut HashMap::new())')
        s+='''
#[cfg(test)]mod conversion_storage_tests {
 use super::*;
 #[test]fn context_branches_cannot_observe_sibling_extension(){
  let parent=Rc::new(vec![TypeValue::Sort(crate::level::LevelTerm::Zero)]);
  let original=parent.clone();let mut a=parent.clone();let mut b=parent.clone();
  Rc::make_mut(&mut a).push(TypeValue::Sort(crate::level::LevelTerm::param("a")));
  Rc::make_mut(&mut b).push(TypeValue::Sort(crate::level::LevelTerm::param("b")));
  assert_eq!(original.len(),1);assert_eq!(parent.len(),1);assert_ne!(a[1],b[1]);assert_eq!(a[0],b[0]);
 }
 #[test]fn reflexive_conversion_preserves_zero_budget_behavior(){
  let es=crate::id::IdTable::default();let ls=crate::id::IdTable::default();let env=crate::environment::Environment::empty();
  let checker=TypeChecker::new(&es,&ls,&env);let value=TypeValue::Sort(crate::level::LevelTerm::Zero);
  assert!(convert_with_policy(&checker,&value,&value,0,DeltaPolicy::GuardedSemanticFallback).is_proven());
 }
}
'''
    return s
