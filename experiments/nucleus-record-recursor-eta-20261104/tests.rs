#[cfg(test)]
mod record_recursor_eta_tests {
 use super::*;
 use crate::environment::ConstantDecl;
 use crate::machine::{ProjectionSpec,RecursorReduction,RecursorRule};
 fn tables()->(IdTable<ExprId,Expr>,IdTable<LevelId,Level>){
  let mut e=IdTable::default();let mut l=IdTable::default();l.insert(LevelId(0),Level::Zero).unwrap();l.insert(LevelId(1),Level::Succ(LevelId(0))).unwrap();
  for(id,node)in[(0,Expr::Sort(LevelId(0))),(1,Expr::Sort(LevelId(1))),(2,Expr::Const{name:NameId(900),levels:vec![]}),(3,Expr::BVar(0)),(4,Expr::Lam{domain:ExprId(0),body:ExprId(3)}),(5,Expr::Lam{domain:ExprId(0),body:ExprId(4)}),(6,Expr::Const{name:NameId(903),levels:vec![]})]{e.insert(ExprId(id),node).unwrap();}(e,l)
 }
 // The unit fixture supplies a trusted layout directly. In particular its
 // Prop case deliberately overstates eta metadata to test the independent
 // instantiated-sort guard; source admission is tested by source controls.
 fn environment(prop:bool)->Environment{
  Environment::empty().extend(NameId(900),ConstantDecl::axiom(vec![],ExprId(if prop{0}else{1}))).unwrap()
   .extend(NameId(903),ConstantDecl::axiom(vec![],ExprId(1))).unwrap()
   .extend(NameId(902),ConstantDecl::axiom(vec![],ExprId(2))).unwrap()
   .extend(NameId(901),ConstantDecl::recursor(vec![],ExprId(0))).unwrap()
   .install_projection_spec(NameId(900),ProjectionSpec{constructor:NameId(902),num_params:0,field_types:vec![],eta_expandable:true}).unwrap()
   .install_recursor_reduction(NameId(901),RecursorReduction{k:false,num_params:0,num_indices:0,level_params:vec![],rules:vec![RecursorRule{constructor:NameId(902),constructor_level_params:vec![],num_params:0,num_fields:0,rhs:ExprId(5)}]}).unwrap()
 }
 fn subject()->Neutral{
  Neutral{head:NeutralHead::Const{name:NameId(901),levels:vec![]},spine:vec![Closure::new(ExprId(0),EnvFrame::empty()),Closure::new(ExprId(0),EnvFrame::empty()),Closure::new(ExprId(3),EnvFrame::empty().extend_free(FreeId(0)))]}
 }
 #[test]fn admitted_record_eta_reserves_its_prerequisites_from_the_caller(){
  let(e,l)=tables();let env=environment(false);let checker=TypeChecker::new(&e,&l,&env);let ctx=vec![TypeValue::Term(Closure::new(ExprId(2),EnvFrame::empty()))];let mut budget=16384;
  assert!(checker.checked_record_recursor_eta(&subject(),&ctx,&mut budget).is_some());assert_eq!(budget,8192);
 }
 #[test]fn proposition_owner_cannot_gain_data_eta_from_layout_metadata(){
  let(e,l)=tables();let env=environment(true);let checker=TypeChecker::new(&e,&l,&env);let ctx=vec![TypeValue::Term(Closure::new(ExprId(2),EnvFrame::empty()))];let mut budget=16384;
  assert!(checker.checked_record_recursor_eta(&subject(),&ctx,&mut budget).is_none());assert_eq!(budget,8192);
 }
 #[test]fn record_eta_checks_the_actual_owner_and_restores_its_trial_scope(){
  let(e,l)=tables();let env=environment(false);let checker=TypeChecker::new(&e,&l,&env);let mut budget=32768;
  assert!(checker.checked_record_recursor_eta(&subject(),&[TypeValue::Term(Closure::new(ExprId(6),EnvFrame::empty()))],&mut budget).is_none());
  assert!(checker.checked_record_recursor_eta(&subject(),&[TypeValue::Term(Closure::new(ExprId(2),EnvFrame::empty()))],&mut budget).is_some());
 }
}
