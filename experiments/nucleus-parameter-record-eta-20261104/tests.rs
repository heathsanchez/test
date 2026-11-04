#[cfg(test)]
mod eta_projection_shape_tests {
 use super::*;
 fn source()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>){
  let mut e=IdTable::default();for(id,node)in[(0,Expr::BVar(0)),(1,Expr::BVar(1)),(2,Expr::Proj{type_name:NameId(900),index:0,structure:ExprId(1)}),(3,Expr::Proj{type_name:NameId(900),index:0,structure:ExprId(0)}),(4,Expr::Proj{type_name:NameId(901),index:0,structure:ExprId(1)}),(5,Expr::Proj{type_name:NameId(900),index:1,structure:ExprId(1)})]{e.insert(ExprId(id),node).unwrap();}(e,IdTable::default())
 }
 fn target(free:u64)->Neutral{Neutral{head:NeutralHead::Free(FreeId(free)),spine:vec![]}}
 // These are structural projection-witness checks only. The caller still
 // proves the actual owner, universe instance, parameters and eta eligibility.
 #[test]fn a_literal_source_projection_witnesses_its_exact_receiver_field(){
  let(e,l)=source();let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let frame=EnvFrame::empty().extend_free(FreeId(0)).extend_free(FreeId(1));
  assert!(checker.certified_eta_projection_field(&Closure::new(ExprId(2),frame),NameId(900),0,&target(0),4,256));
 }
 #[test]fn an_already_evaluated_captured_projection_keeps_the_same_witness(){
  let(e,l)=source();let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let value=Neutral{head:NeutralHead::Projection{type_name:NameId(900),index:0,structure:Box::new(target(0))},spine:vec![]};
  assert!(checker.certified_eta_projection_field(&Closure::new(ExprId(0),EnvFrame::empty().extend_neutral(value)),NameId(900),0,&target(0),4,256));
 }
 #[test]fn literal_projection_never_substitutes_a_different_owner_field_or_receiver(){
  let(e,l)=source();let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let frame=EnvFrame::empty().extend_free(FreeId(0)).extend_free(FreeId(1));
  for id in [3,4,5]{assert!(!checker.certified_eta_projection_field(&Closure::new(ExprId(id),frame.clone()),NameId(900),0,&target(0),4,256));}
 }
 #[test]fn applied_captured_projection_is_not_an_unapplied_field_witness(){
  let(e,l)=source();let env=Environment::empty();let checker=TypeChecker::new(&e,&l,&env);let value=Neutral{head:NeutralHead::Projection{type_name:NameId(900),index:0,structure:Box::new(target(0))},spine:vec![Closure::new(ExprId(0),EnvFrame::empty())]};
  assert!(!checker.certified_eta_projection_field(&Closure::new(ExprId(0),EnvFrame::empty().extend_neutral(value)),NameId(900),0,&target(0),4,256));
 }
}
